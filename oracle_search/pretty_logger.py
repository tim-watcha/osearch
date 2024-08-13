from pprint import pformat

from loguru import logger


def pretty_message(width, *args, **kwargs):
    """
    포맷된 메시지를 생성합니다.

    Args:
        width (int): 메시지의 너비.
        *args: 포맷할 인수들.
        **kwargs: 포맷할 키워드 인수들.

    Returns:
        str: 포맷된 메시지.
    """
    def is_primitive(val):
        return isinstance(val, (str, int, float, bool, type(None)))

    pretty_args = [pformat(arg, width=width, compact=True) if not is_primitive(arg) else arg for arg in args]
    pretty_kwargs = {k: pformat(v, width=width, compact=True) if not is_primitive(v) else v for k, v in kwargs.items()}

    parts = []
    if pretty_args:
        parts.append("\n".join(pretty_args))
    if pretty_kwargs:
        parts.append("\n".join(f"{k}={v}" for k, v in pretty_kwargs.items()))
    return "\n".join(parts)


class PrettyLogger:
    def __init__(self, default_width=160):
        """
        PrettyLogger 인스턴스를 초기화합니다.

        Args:
            default_width (int): 기본 메시지 너비.
        """
        self.default_width = default_width

    def log(self, level, *args, width=None, depth=0, **kwargs):
        """
        주어진 로그 레벨에 따라 메시지를 로그합니다.

        Args:
            level (str): 로그 레벨.
            *args: 로그할 인수들.
            width (int, optional): 메시지 너비. 기본값은 None.
            depth (int): 로그 깊이.
            **kwargs: 로그할 키워드 인수들.
        """
        if width is None:
            width = self.default_width
        message = pretty_message(width, *args, **kwargs)
        logger.opt(depth=1 + depth).log(level, message)

    def debug(self, *args, width=None, **kwargs):
        """
        DEBUG 레벨로 메시지를 로그합니다.

        Args:
            *args: 로그할 인수들.
            width (int, optional): 메시지 너비. 기본값은 None.
            **kwargs: 로그할 키워드 인수들.
        """
        self.log("DEBUG", *args, width=width, depth=1, **kwargs)

    def info(self, *args, width=None, **kwargs):
        """
        INFO 레벨로 메시지를 로그합니다.

        Args:
            *args: 로그할 인수들.
            width (int, optional): 메시지 너비. 기본값은 None.
            **kwargs: 로그할 키워드 인수들.
        """
        self.log("INFO", *args, width=width, depth=1, **kwargs)

    def warning(self, *args, width=None, **kwargs):
        """
        WARNING 레벨로 메시지를 로그합니다.

        Args:
            *args: 로그할 인수들.
            width (int, optional): 메시지 너비. 기본값은 None.
            **kwargs: 로그할 키워드 인수들.
        """
        self.log("WARNING", *args, width=width, depth=1, **kwargs)

    def error(self, *args, width=None, **kwargs):
        """
        ERROR 레벨로 메시지를 로그합니다.

        Args:
            *args: 로그할 인수들.
            width (int, optional): 메시지 너비. 기본값은 None.
            **kwargs: 로그할 키워드 인수들.
        """
        self.log("ERROR", *args, width=width, depth=1, **kwargs)

    def critical(self, *args, width=None, **kwargs):
        """
        CRITICAL 레벨로 메시지를 로그합니다.

        Args:
            *args: 로그할 인수들.
            width (int, optional): 메시지 너비. 기본값은 None.
            **kwargs: 로그할 키워드 인수들.
        """
        self.log("CRITICAL", *args, width=width, depth=1, **kwargs)


def setup_logger(minimum_level="DEBUG", default_width=160):
    """
    로거를 설정합니다.

    Args:
        minimum_level (str): 최소 로그 레벨.
        default_width (int): 기본 메시지 너비.

    Returns:
        PrettyLogger: 설정된 로거 인스턴스.
    """
    format_str = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> - <level>{level: <8}</level> - "
        'File "<cyan>{file.path}</cyan>", line <cyan>{line}</cyan> -\n{message}'
    )
    logger.remove()
    logger.add(
        lambda msg: print(msg),
        format=format_str,
        level=minimum_level,
        colorize=True,
    )
    return PrettyLogger(default_width=default_width)
