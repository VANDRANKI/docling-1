import sys
from pathlib import Path
from loguru import logger
from typing import Union, Optional
from datetime import datetime

class RAGLogger:
    """
    Custom logger class for the RAG system with advanced error tracking
    and structured logging capabilities.
    """
    
    def __init__(
        self,
        log_file: Union[str, Path] = "logs/rag_system.log",
        rotation: str = "500 MB",
        retention: str = "10 days",
        level: str = "INFO"
    ):
        """
        Initialize the logger with custom configuration.
        
        Args:
            log_file: Path to the log file
            rotation: When to rotate the log file
            retention: How long to keep log files
            level: Minimum logging level
        """
        # Initialize log file and directories
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Create logs directory if it doesn't exist
        Path("logs").mkdir(parents=True, exist_ok=True)
        
        # Remove default logger
        logger.remove()
        
        # Add console handler with custom format
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>",
            level=level,
            colorize=True
        )
        
        # Add file handler with detailed format
        logger.add(
            str(self.log_file),
            rotation=rotation,
            retention=retention,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
            "{name}:{function}:{line} | {message} | {extra}",
            level=level,
            backtrace=True,
            diagnose=True
        )
    
    def get_logger(self):
        """Get the configured logger instance."""
        return logger
    
    @staticmethod
    def format_error(error: Exception) -> str:
        """
        Format error details for logging.
        
        Args:
            error: The exception to format
            
        Returns:
            Formatted error message with traceback
        """
        import traceback
        return f"""
Error Type: {type(error).__name__}
Error Message: {str(error)}
Traceback:
{traceback.format_exc()}
        """

class ErrorTracker:
    """
    Track and manage errors in the RAG system.
    """
    
    def __init__(self, logger_instance: RAGLogger):
        self.logger = logger_instance.get_logger()
        self.errors = []
        
    def record_error(
        self,
        error: Exception,
        component: str,
        severity: str = "ERROR",
        context: Optional[dict] = None
    ):
        """
        Record an error with context.
        
        Args:
            error: The exception to record
            component: Which component raised the error
            severity: Error severity level
            context: Additional context about the error
        """
        error_info = {
            "timestamp": datetime.now().isoformat(),
            "type": type(error).__name__,
            "message": str(error),
            "component": component,
            "severity": severity,
            "context": context or {}
        }
        
        self.errors.append(error_info)
        
        # Log the error with context
        with self.logger.contextualize(**error_info):
            self.logger.log(
                severity,
                f"Error in {component}: {error}\nContext: {context}"
            )
    
    def get_error_summary(self) -> dict:
        """
        Get a summary of recorded errors.
        
        Returns:
            Dictionary with error statistics
        """
        if not self.errors:
            return {"total_errors": 0}
        
        return {
            "total_errors": len(self.errors),
            "error_types": {
                error_type: len([e for e in self.errors if e["type"] == error_type])
                for error_type in set(e["type"] for e in self.errors)
            },
            "components_affected": {
                component: len([e for e in self.errors if e["component"] == component])
                for component in set(e["component"] for e in self.errors)
            },
            "severity_distribution": {
                severity: len([e for e in self.errors if e["severity"] == severity])
                for severity in set(e["severity"] for e in self.errors)
            }
        }

# Example usage:
if __name__ == "__main__":
    # Initialize logger
    rag_logger = RAGLogger()
    logger = rag_logger.get_logger()
    error_tracker = ErrorTracker(rag_logger)
    
    # Example logging
    try:
        raise ValueError("Example error")
    except Exception as e:
        error_tracker.record_error(
            error=e,
            component="main",
            context={"operation": "example"}
        )
        
    # Print error summary
    print(error_tracker.get_error_summary())
