from sqlalchemy import create_engine, Column, Integer, String, Date
from sqlalchemy.orm import declarative_base, sessionmaker
import datetime

# 1. 修复警告：使用新的 declarative_base 导入
Base = declarative_base()

# 2. 创建数据库引擎
# 替换为你的数据库文件路径
db_path = 'sqlite:///D:/XRDocument/Code/checkin/instance/users.db'
engine = create_engine(db_path, echo=True)

# 3. 定义 SignPeriod 模型
class SignPeriod(Base):
    __tablename__ = 'SignPeriod'  # 确保表名一致
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

# 4. 创建表（如果不存在）
def create_table():
    """创建 SignPeriod 表"""
    Base.metadata.create_all(engine)
    print("检查并创建表完成。")

# 5. 查看数据函数
def view_data():
    """查询并打印 SignPeriod 表中的所有数据"""
    periods = session.query(SignPeriod).all()
    if periods:
        for period in periods:
            print(f"ID: {period.id}, Name: {period.name}, Start Date: {period.start_date}, End Date: {period.end_date}")
    else:
        print("表中没有数据。")

# 6. 修改数据函数
def modify_data(period_id, new_name=None, new_start_date=None, new_end_date=None):
    """根据 ID 修改 SignPeriod 表中的记录"""
    period = session.query(SignPeriod).filter_by(id=period_id).first()
    if period:
        if new_name:
            period.name = new_name
        if new_start_date:
            period.start_date = new_start_date
        if new_end_date:
            period.end_date = new_end_date
        session.commit()
        print(f"ID 为 {period_id} 的记录已更新。")
    else:
        print(f"未找到 ID 为 {period_id} 的记录。")

# 7. 创建会话
Session = sessionmaker(bind=engine)
session = Session()

# 示例用法
if __name__ == "__main__":
    try:
        # 确保表存在
        create_table()

        # 查看所有数据
        print("\n当前数据：")
        view_data()


        # # 示例：修改 ID 为 1 的记录
        # modify_data(
        #     period_id=1,
        #     new_name='New Period',
        #     new_start_date=datetime.date(2023, 1, 1),
        #     new_end_date=datetime.date(2023, 12, 31)
        # )

        # 再次查看数据以确认修改
        # print("\n修改后的数据：")
        # view_data()

    except Exception as e:
        print(f"发生错误：{e}")
    finally:
        session.close()