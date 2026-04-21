from datetime import datetime, date, time, timedelta
from calendar import monthrange
import time

"""
日期工具类（Python3版）
完全对应原Java DateUtil功能
"""
class DateUtil:
    # 日期格式常量
    Y = "%Y"
    Y_M = "%Y-%m"
    Y_M_D = "%Y-%m-%d"
    Y_M_D_H_M_S = "%Y-%m-%d %H:%M:%S"
    H_M_S = "%H:%M:%S"
    YMDHMS = "%Y%m%d%H%M%S"
    YMD = "%Y%m%d"

    @staticmethod
    def week_first_day(date_obj: date) -> date:
        """
        周的第一天（周一）
        """
        return date_obj - timedelta(days=date_obj.weekday())

    @staticmethod
    def week_last_day(date_obj: date) -> date:
        """
        周的最后一天（周日）
        """
        return DateUtil.week_first_day(date_obj) + timedelta(days=6)

    @staticmethod
    def get_date_week(date_obj: date) -> int:
        """
        获取当前日期一年中的第几周（周一为一周开始）
        """
        return date_obj.isocalendar()[1]

    @staticmethod
    def day_of_start_time(date_obj: date) -> datetime:
        """
        某天开始时间 00:00:00
        """
        return datetime.combine(date_obj, time.min)

    @staticmethod
    def day_of_end_time(date_obj: date) -> datetime:
        """
        某天结束时间 23:59:59
        """
        return datetime.combine(date_obj, time.max)

    @staticmethod
    def first_day_of_month(date_obj: date) -> date:
        """
        月的第一天
        """
        return date_obj.replace(day=1)

    @staticmethod
    def last_day_of_month(date_obj: date) -> date:
        """
        月的最后一天
        """
        return date_obj.replace(day=monthrange(date_obj.year, date_obj.month)[1])

    @staticmethod
    def first_day_of_year(date_obj: date) -> date:
        """
        年的第一天
        """
        return date_obj.replace(month=1, day=1)

    @staticmethod
    def last_day_of_year(date_obj: date) -> date:
        """
        年的最后一天
        """
        return date_obj.replace(month=12, day=31)

    # ------------------------------ 字符串与日期互转 ------------------------------
    @staticmethod
    def string_to_local_date(date_str: str, date_format=Y_M_D) -> date:
        """
        字符串转date对象
        """
        return datetime.strptime(date_str, date_format).date()

    @staticmethod
    def string_to_local_date_time(date_str: str, date_format=Y_M_D_H_M_S) -> datetime:
        """
        字符串转datetime对象
        """
        return datetime.strptime(date_str, date_format)

    @staticmethod
    def local_date_to_string(date_obj: date, date_format=Y_M_D) -> str:
        """
        date对象转字符串
        """
        return date_obj.strftime(date_format)

    @staticmethod
    def local_date_time_to_string(dt_obj: datetime, date_format=Y_M_D_H_M_S) -> str:
        """
        datetime对象转字符串
        """
        return dt_obj.strftime(date_format)

    # ------------------------------ 年月/年份转换 ------------------------------
    @staticmethod
    def string_to_year_month(date_str: str, date_format=Y_M) -> tuple:
        """
        字符串转(年,月)
        """
        dt = datetime.strptime(date_str, date_format)
        return dt.year, dt.month

    @staticmethod
    def year_month_to_local_date(date_str: str, date_format=Y_M, day=1) -> date:
        """
        年月字符串转date
        """
        dt = datetime.strptime(date_str, date_format)
        return date(dt.year, dt.month, day)

    @staticmethod
    def string_to_year(date_str: str, date_format=Y) -> int:
        """
        字符串转年份
        """
        return datetime.strptime(date_str, date_format).year

    @staticmethod
    def year_to_local_date(year: int, month=1, day=1) -> date:
        """
        年份转date
        """
        return date(year, month, day)

    # ------------------------------ 天数计算 ------------------------------
    @staticmethod
    def count_days_in_month(date_obj: date, month=None) -> int:
        """
        计算指定月份天数
        """
        if month is None:
            month = date_obj.month
        return monthrange(date_obj.year, month)[1]

    @staticmethod
    def calc_date_days(start: date, end: date) -> int:
        """
        计算两个日期相差天数
        """
        return (end - start).days

    # ------------------------------ 时间戳 ------------------------------
    @staticmethod
    def get_now_mill() -> str:
        """
        获取当前时间毫秒数
        """
        return str(int(time.time() * 1000))

    @staticmethod
    def get_now_date() -> date:
        """获取当前时间（年月日）"""
        return date.today()

    @staticmethod
    def get_now_datetime() -> datetime:
        """获取当前时间（年月日时分秒）"""
        return datetime.now()