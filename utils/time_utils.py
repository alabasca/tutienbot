import datetime
import time
from typing import Dict, Any, Optional, Tuple, Union


def get_current_time() -> datetime.datetime:
    """Lấy thời gian hiện tại"""
    return datetime.datetime.now()


def get_time_diff(time1: datetime.datetime, time2: datetime.datetime) -> float:
    """Lấy khoảng cách thời gian giữa hai thời điểm (tính bằng giây)"""
    return abs((time2 - time1).total_seconds())


def get_time_diff_str(time1: datetime.datetime, time2: datetime.datetime) -> str:
    """Lấy khoảng cách thời gian giữa hai thời điểm (định dạng chuỗi)"""
    seconds = get_time_diff(time1, time2)
    return format_seconds(seconds)


def format_seconds(seconds: float) -> str:
    """Định dạng số giây thành chuỗi thời gian"""
    seconds = int(seconds)

    # Nếu ít hơn 1 phút
    if seconds < 60:
        return f"{seconds} giây"

    # Nếu ít hơn 1 giờ
    minutes, seconds = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes} phút {seconds} giây"

    # Nếu ít hơn 1 ngày
    hours, minutes = divmod(minutes, 60)
    if hours < 24:
        return f"{hours} giờ {minutes} phút {seconds} giây"

    # Nếu nhiều hơn 1 ngày
    days, hours = divmod(hours, 24)
    return f"{days} ngày {hours} giờ {minutes} phút {seconds} giây"


def is_same_day(time1: datetime.datetime, time2: datetime.datetime) -> bool:
    """Kiểm tra hai thời điểm có cùng ngày không"""
    return (time1.year == time2.year and
            time1.month == time2.month and
            time1.day == time2.day)


def get_next_day(current_time: datetime.datetime) -> datetime.datetime:
    """Lấy thời điểm đầu ngày tiếp theo"""
    next_day = current_time.date() + datetime.timedelta(days=1)
    return datetime.datetime.combine(next_day, datetime.time.min)


def get_time_until_next_day(current_time: datetime.datetime) -> float:
    """Lấy thời gian đến đầu ngày tiếp theo (tính bằng giây)"""
    next_day = get_next_day(current_time)
    return get_time_diff(current_time, next_day)


def is_expired(timestamp: Union[str, datetime.datetime], duration_seconds: float) -> bool:
    """Kiểm tra xem một thời điểm đã hết hạn chưa"""
    now = get_current_time()

    # Chuyển đổi chuỗi thời gian thành đối tượng datetime nếu cần
    if isinstance(timestamp, str):
        timestamp = datetime.datetime.fromisoformat(timestamp)

    # Tính thời gian đã trôi qua
    elapsed_seconds = get_time_diff(timestamp, now)

    # Kiểm tra hết hạn
    return elapsed_seconds >= duration_seconds


def get_time_left(timestamp: Union[str, datetime.datetime], duration_seconds: float) -> float:
    """Lấy thời gian còn lại (tính bằng giây)"""
    now = get_current_time()

    # Chuyển đổi chuỗi thời gian thành đối tượng datetime nếu cần
    if isinstance(timestamp, str):
        timestamp = datetime.datetime.fromisoformat(timestamp)

    # Tính thời gian đã trôi qua
    elapsed_seconds = get_time_diff(timestamp, now)

    # Tính thời gian còn lại
    time_left = duration_seconds - elapsed_seconds

    # Nếu đã hết hạn, trả về 0
    return max(0, time_left)


def get_time_left_str(timestamp: Union[str, datetime.datetime], duration_seconds: float) -> str:
    """Lấy thời gian còn lại (định dạng chuỗi)"""
    time_left_seconds = get_time_left(timestamp, duration_seconds)
    return format_seconds(time_left_seconds)


def format_timestamp(timestamp: Union[str, datetime.datetime], format_str: str = "%d/%m/%Y %H:%M:%S") -> str:
    """Định dạng thời gian thành chuỗi"""
    # Chuyển đổi chuỗi thời gian thành đối tượng datetime nếu cần
    if isinstance(timestamp, str):
        timestamp = datetime.datetime.fromisoformat(timestamp)

    return timestamp.strftime(format_str)


def get_vietnam_time() -> datetime.datetime:
    """Lấy thời gian theo múi giờ Việt Nam (UTC+7)"""
    utc_time = datetime.datetime.utcnow()
    vietnam_offset = datetime.timedelta(hours=7)
    return utc_time + vietnam_offset


def get_vietnamese_date_string() -> str:
    """Lấy chuỗi ngày tháng theo định dạng tiếng Việt"""
    now = get_vietnam_time()

    weekdays = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
    weekday = weekdays[now.weekday()]

    return f"{weekday}, ngày {now.day} tháng {now.month} năm {now.year}"


def get_cooldown_status(last_timestamp: Optional[Union[str, datetime.datetime]], cooldown_seconds: float) -> Tuple[
    bool, float]:
    """
    Kiểm tra trạng thái cooldown và thời gian còn lại

    Trả về: (đang_trong_cooldown, thời_gian_còn_lại)
    """
    # Nếu không có timestamp cuối, không có cooldown
    if last_timestamp is None:
        return False, 0

    # Lấy thời gian còn lại
    time_left = get_time_left(last_timestamp, cooldown_seconds)

    # Kiểm tra xem có đang trong cooldown không
    is_in_cooldown = time_left > 0

    return is_in_cooldown, time_left