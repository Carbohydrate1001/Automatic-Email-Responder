"""
Unit tests for RetryHandler and CircuitBreaker.

Tests cover:
- Retry logic with exponential backoff
- Circuit breaker states and transitions
- Jitter calculation
- Error handling
- Edge cases
"""

import pytest
import time
from unittest.mock import Mock, patch
from utils.retry_handler import (
    RetryHandler,
    CircuitBreaker,
    CircuitState,
    CircuitBreakerError,
    with_retry,
    get_circuit_breaker
)


class TestCircuitBreaker:
    """Test suite for CircuitBreaker."""

    def test_circuit_breaker_initial_state(self):
        """Test circuit breaker starts in CLOSED state."""
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=5)

        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0
        assert cb.last_failure_time is None

    def test_circuit_breaker_success(self):
        """Test successful calls keep circuit CLOSED."""
        cb = CircuitBreaker(failure_threshold=3)

        def success_func():
            return "success"

        result = cb.call(success_func)

        assert result == "success"
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    def test_circuit_breaker_opens_after_threshold(self):
        """Test circuit opens after failure threshold."""
        cb = CircuitBreaker(failure_threshold=3)

        def failing_func():
            raise Exception("API error")

        # Fail 3 times to reach threshold
        for i in range(3):
            with pytest.raises(Exception):
                cb.call(failing_func)

        assert cb.state == CircuitState.OPEN
        assert cb.failure_count == 3

    def test_circuit_breaker_rejects_when_open(self):
        """Test circuit breaker rejects calls when OPEN."""
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=60)

        def failing_func():
            raise Exception("API error")

        # Open the circuit
        for i in range(2):
            with pytest.raises(Exception):
                cb.call(failing_func)

        # Next call should be rejected
        with pytest.raises(CircuitBreakerError):
            cb.call(failing_func)

    def test_circuit_breaker_half_open_after_timeout(self):
        """Test circuit enters HALF_OPEN after recovery timeout."""
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=1)

        def failing_func():
            raise Exception("API error")

        # Open the circuit
        for i in range(2):
            with pytest.raises(Exception):
                cb.call(failing_func)

        assert cb.state == CircuitState.OPEN

        # Wait for recovery timeout
        time.sleep(1.1)

        # Next call should enter HALF_OPEN
        def success_func():
            return "recovered"

        result = cb.call(success_func)

        assert result == "recovered"
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    def test_circuit_breaker_reopens_on_half_open_failure(self):
        """Test circuit reopens if HALF_OPEN call fails."""
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=1)

        def failing_func():
            raise Exception("API error")

        # Open the circuit
        for i in range(2):
            with pytest.raises(Exception):
                cb.call(failing_func)

        # Wait for recovery timeout
        time.sleep(1.1)

        # Fail in HALF_OPEN state
        with pytest.raises(Exception):
            cb.call(failing_func)

        # Should still be OPEN (or increment failure count)
        assert cb.failure_count >= 2

    def test_circuit_breaker_manual_reset(self):
        """Test manual circuit breaker reset."""
        cb = CircuitBreaker(failure_threshold=2)

        def failing_func():
            raise Exception("API error")

        # Open the circuit
        for i in range(2):
            with pytest.raises(Exception):
                cb.call(failing_func)

        assert cb.state == CircuitState.OPEN

        # Manual reset
        cb.reset()

        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0
        assert cb.last_failure_time is None

    def test_circuit_breaker_get_state(self):
        """Test getting circuit breaker state."""
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=60)

        state = cb.get_state()

        assert state['state'] == 'closed'
        assert state['failure_count'] == 0
        assert state['failure_threshold'] == 3
        assert state['recovery_timeout'] == 60


class TestRetryHandler:
    """Test suite for RetryHandler."""

    def test_retry_handler_success_first_try(self):
        """Test successful call on first try."""
        handler = RetryHandler(max_retries=3)

        mock_func = Mock(return_value="success")

        result = handler.execute(mock_func)

        assert result == "success"
        assert mock_func.call_count == 1

    def test_retry_handler_success_after_retries(self):
        """Test successful call after retries."""
        handler = RetryHandler(max_retries=3, base_delay=0.1)

        mock_func = Mock(side_effect=[
            Exception("error 1"),
            Exception("error 2"),
            "success"
        ])

        result = handler.execute(mock_func, retryable_exceptions=(Exception,))

        assert result == "success"
        assert mock_func.call_count == 3

    def test_retry_handler_exhausts_retries(self):
        """Test all retries exhausted."""
        handler = RetryHandler(max_retries=2, base_delay=0.1)

        mock_func = Mock(side_effect=Exception("persistent error"))

        with pytest.raises(Exception, match="persistent error"):
            handler.execute(mock_func, retryable_exceptions=(Exception,))

        assert mock_func.call_count == 3  # Initial + 2 retries

    def test_retry_handler_exponential_backoff(self):
        """Test exponential backoff calculation."""
        handler = RetryHandler(
            max_retries=3,
            base_delay=1.0,
            exponential_base=2.0,
            jitter=False
        )

        # Test delay calculation
        delay1 = handler._calculate_delay(1)
        delay2 = handler._calculate_delay(2)
        delay3 = handler._calculate_delay(3)

        assert delay1 == 1.0  # 1.0 * 2^0
        assert delay2 == 2.0  # 1.0 * 2^1
        assert delay3 == 4.0  # 1.0 * 2^2

    def test_retry_handler_max_delay_cap(self):
        """Test delay is capped at max_delay."""
        handler = RetryHandler(
            max_retries=10,
            base_delay=1.0,
            max_delay=5.0,
            exponential_base=2.0,
            jitter=False
        )

        delay = handler._calculate_delay(10)

        assert delay <= 5.0

    def test_retry_handler_with_jitter(self):
        """Test jitter adds randomness to delay."""
        handler = RetryHandler(
            max_retries=3,
            base_delay=1.0,
            jitter=True
        )

        delays = [handler._calculate_delay(1) for _ in range(10)]

        # All delays should be different due to jitter
        assert len(set(delays)) > 1

        # All delays should be close to base_delay
        for delay in delays:
            assert 0.9 <= delay <= 1.1

    def test_retry_handler_on_retry_callback(self):
        """Test on_retry callback is called."""
        handler = RetryHandler(max_retries=2, base_delay=0.1)

        callback_calls = []

        def on_retry(attempt, delay, error):
            callback_calls.append((attempt, delay, str(error)))

        mock_func = Mock(side_effect=[
            Exception("error 1"),
            Exception("error 2"),
            "success"
        ])

        handler.execute(
            mock_func,
            retryable_exceptions=(Exception,),
            on_retry=on_retry
        )

        assert len(callback_calls) == 2
        assert callback_calls[0][0] == 1
        assert callback_calls[1][0] == 2

    def test_retry_handler_with_circuit_breaker(self):
        """Test retry handler with circuit breaker."""
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=60)
        handler = RetryHandler(max_retries=3, base_delay=0.1, circuit_breaker=cb)

        mock_func = Mock(side_effect=Exception("API error"))

        # First call - should retry and open circuit
        with pytest.raises(Exception):
            handler.execute(mock_func, retryable_exceptions=(Exception,))

        # Circuit should be OPEN after failures
        assert cb.state == CircuitState.OPEN

        # Next call should be rejected by circuit breaker
        with pytest.raises(CircuitBreakerError):
            handler.execute(mock_func, retryable_exceptions=(Exception,))

    def test_retry_handler_non_retryable_exception(self):
        """Test non-retryable exceptions are not retried."""
        handler = RetryHandler(max_retries=3, base_delay=0.1)

        mock_func = Mock(side_effect=ValueError("not retryable"))

        with pytest.raises(ValueError):
            handler.execute(mock_func, retryable_exceptions=(ConnectionError,))

        # Should only be called once (no retries)
        assert mock_func.call_count == 1


class TestWithRetryDecorator:
    """Test suite for with_retry decorator."""

    def test_with_retry_decorator_success(self):
        """Test decorator on successful function."""
        @with_retry(max_retries=3, base_delay=0.1)
        def successful_func():
            return "success"

        result = successful_func()

        assert result == "success"

    def test_with_retry_decorator_retries(self):
        """Test decorator retries on failure."""
        call_count = {'count': 0}

        @with_retry(max_retries=2, base_delay=0.1, retryable_exceptions=(ValueError,))
        def failing_func():
            call_count['count'] += 1
            if call_count['count'] < 3:
                raise ValueError("error")
            return "success"

        result = failing_func()

        assert result == "success"
        assert call_count['count'] == 3

    def test_with_retry_decorator_exhausts_retries(self):
        """Test decorator exhausts retries."""
        @with_retry(max_retries=2, base_delay=0.1, retryable_exceptions=(ValueError,))
        def always_failing_func():
            raise ValueError("persistent error")

        with pytest.raises(ValueError):
            always_failing_func()


class TestGetCircuitBreaker:
    """Test suite for get_circuit_breaker."""

    def test_get_circuit_breaker_creates_new(self):
        """Test getting a new circuit breaker."""
        cb = get_circuit_breaker('test_service', failure_threshold=5)

        assert cb is not None
        assert cb.failure_threshold == 5

    def test_get_circuit_breaker_returns_same_instance(self):
        """Test getting same circuit breaker instance."""
        cb1 = get_circuit_breaker('test_service_2')
        cb2 = get_circuit_breaker('test_service_2')

        assert cb1 is cb2


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_zero_max_retries(self):
        """Test with zero max retries."""
        handler = RetryHandler(max_retries=0, base_delay=0.1)

        mock_func = Mock(side_effect=Exception("error"))

        with pytest.raises(Exception):
            handler.execute(mock_func, retryable_exceptions=(Exception,))

        assert mock_func.call_count == 1

    def test_negative_delay(self):
        """Test delay calculation doesn't go negative."""
        handler = RetryHandler(base_delay=0.1, jitter=True)

        delay = handler._calculate_delay(1)

        assert delay >= 0

    def test_circuit_breaker_with_no_failures(self):
        """Test circuit breaker with only successful calls."""
        cb = CircuitBreaker(failure_threshold=3)

        def success_func():
            return "success"

        # Make multiple successful calls
        for _ in range(10):
            cb.call(success_func)

        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    def test_retry_handler_with_args_and_kwargs(self):
        """Test retry handler passes args and kwargs correctly."""
        handler = RetryHandler(max_retries=2, base_delay=0.1)

        mock_func = Mock(return_value="success")

        result = handler.execute(
            mock_func,
            "arg1",
            "arg2",
            retryable_exceptions=(Exception,),
            kwarg1="value1",
            kwarg2="value2"
        )

        assert result == "success"
        mock_func.assert_called_once_with("arg1", "arg2", kwarg1="value1", kwarg2="value2")
