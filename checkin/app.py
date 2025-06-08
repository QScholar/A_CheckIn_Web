from flask import Flask, render_template, redirect, url_for, flash, request, abort, Response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, DateField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from flask_bcrypt import Bcrypt
from datetime import date
from sqlalchemy import func,and_
import os
import io
import csv

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Lxr0901'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['MAX_CONTENT_LENGTH'] = 4 * 1024 * 1024  # 最大上传文件限制 4MB

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
bcrypt = Bcrypt(app)

# 用户模型
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)  # 学号，最多12字符
    name = db.Column(db.String(20), nullable=False)  # 姓名
    password = db.Column(db.String(60), nullable=False)
    Departments = db.Column(db.String(13), nullable=False)  # 学院
    QQ = db.Column(db.String(14), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

# 打卡记录模型
class CheckInRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(64), nullable=False)
    date = db.Column(db.Date, default=date.today)
    file_path = db.Column(db.String(256), nullable=False)

    __table_args__ = (db.UniqueConstraint('user_id', 'date', name='unique_signin_per_day'),)

# 新增打卡时间段模型
class SignPeriod(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)  # 时间段名称，如“第一阶段”
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)

# 新增例外日期模型（用于定义某一时间段不需要打卡的日期）
class SignInException(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    period_id = db.Column(db.Integer, db.ForeignKey('sign_period.id'), nullable=False)
    exception_date = db.Column(db.Date, nullable=False)
    sign_period = db.relationship('SignPeriod', backref=db.backref('exceptions', lazy=True))

# 修改密码表单
class ChangePasswordForm(FlaskForm):
    username = StringField('学号', validators=[DataRequired()])
    new_password = PasswordField('新密码', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('确认新密码', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('修改密码')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 注册表单
class RegistrationForm(FlaskForm):
    username = StringField('学号', validators=[DataRequired(), Length(min=12, max=12)])
    password = PasswordField('密码', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('确认密码', validators=[DataRequired(), EqualTo('password')])
    name = StringField('姓名', validators=[DataRequired()])
    Departments = SelectField('学院', choices=[], validators=[DataRequired()])
    QQ = StringField('QQ号', validators=[DataRequired()])
    submit = SubmitField('注册')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('学号已被注册，请确保您输入的学号正确，或联系网站管理人员。')

# 登录表单
class LoginForm(FlaskForm):
    username = StringField('学号', validators=[DataRequired()])
    password = PasswordField('密码', validators=[DataRequired()])
    submit = SubmitField('登录')

# 管理员新增打卡时间段的表单
class SignPeriodForm(FlaskForm):
    name = StringField('时间段名称', validators=[DataRequired()])
    start_date = DateField('开始日期', validators=[DataRequired()], format='%Y-%m-%d')
    end_date = DateField('结束日期', validators=[DataRequired()], format='%Y-%m-%d')
    submit = SubmitField('提交')

# 管理员新增例外日期的表单
class ExceptionDateForm(FlaskForm):
    exception_date = DateField('休息日', validators=[DataRequired()], format='%Y-%m-%d')
    submit = SubmitField('添加休息日')

@app.route('/', methods=['GET'])
def index():
    return render_template("index.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    options = [
        '机械工程学院', '材料科学与工程学院', '电气工程学院',
        '信息科学与工程学院（软件学院）', '经济管理学院', '外国语学院',
        '建筑工程与力学学院', '文法学院（公共管理学院）', '马克思主义学院',
        '理学院', '环境与化学工程学院', '艺术与设计学院', '车辆与能源学院',
        '体育学院', '西里西亚智能科学与工程学院', '国际教育学院（欧洲学院）',
        '继续教育学院', '里仁学院'
    ]
    form = RegistrationForm()
    form.Departments.choices = [('', '请选择学院')] + [(opt, opt) for opt in options]
    if form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(
            username=form.username.data,
            password=hashed_pw,
            QQ=form.QQ.data,
            Departments=form.Departments.data,
            name=form.name.data
        )
        db.session.add(user)
        db.session.commit()
        flash('注册成功，请登录。', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('学号或密码错误。', 'danger')
    return render_template('login.html', form=form)

@app.route('/index')
@login_required
def dashboard():
    return render_template(
        'RealIndex.html',
        username=current_user.name,
        sID=current_user.username,
        Dep=current_user.Departments,
        QQ=current_user.QQ
    )

@app.route('/CheckIn', methods=['GET', 'POST'])
@login_required
def CheckIn():
    user_id = current_user.username
    name = current_user.name
    today = date.today()
    # 查询当前打卡时间段
    period = SignPeriod.query.filter(SignPeriod.start_date <= today,
                                       SignPeriod.end_date >= today).first()
    # 设置一个状态变量，传递到模板显示提示信息
    message = ''
    if SignInException.query.filter_by(period_id=period.id, exception_date=today).first():
        message = '今日休息，不用打卡'

    if request.method == 'POST':
        content = request.form.get('contents', '').strip()
        if not period or SignInException.query.filter_by(period_id=period.id, exception_date=today).first():
            flash('非打卡时段','error')
            return redirect(url_for('CheckIn'))
        if not content:
            flash('内容不能为空', 'error')
            return redirect(url_for('CheckIn'))
        if len(content) < 100:
            flash('内容不能少于100字', 'error')
            return redirect(url_for('CheckIn'))
        existing = CheckInRecord.query.filter_by(user_id=user_id, date=today).first()
        if existing:
            flash('今天已经签到过了', 'warning')
            return redirect(url_for('CheckIn'))
        # 保存打卡内容到文本文件
        filename = f"{user_id}_{today}.txt"
        save_dir = os.path.join(app.config['UPLOAD_FOLDER'], user_id, str(today))
        os.makedirs(save_dir, exist_ok=True)
        file_path = os.path.join(save_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        flash('签到成功！', 'success')
        record = CheckInRecord(user_id=user_id, date=today, file_path=file_path)
        db.session.add(record)
        db.session.commit()
        return redirect(url_for('CheckIn'))
    
    count = db.session.query(func.count(CheckInRecord.id)) \
        .filter(CheckInRecord.user_id == current_user.username).scalar()

    # GET 方法时加载用户历史打卡次数，不显示打卡内容
    records = CheckInRecord.query.filter(
    CheckInRecord.user_id == user_id,
    CheckInRecord.date >= SignPeriod.start_date,
    CheckInRecord.date <= SignPeriod.end_date
    )
    return render_template('check_in.html', 
                           records=records, 
                           user_id=user_id, 
                           count=count,
                           name=name, 
                           current_period=period,
                           message=message)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('已登出。', 'info')
    return redirect(url_for('login'))

@app.route('/admin/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if not current_user.is_admin:
        flash('您没有权限访问此页面。', 'danger')
        return redirect(url_for('dashboard'))
    form = ChangePasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            hashed_pw = bcrypt.generate_password_hash(form.new_password.data).decode('utf-8')
            user.password = hashed_pw
            db.session.commit()
            flash('密码已成功修改。', 'success')
        else:
            flash('用户不存在。', 'danger')
        return redirect(url_for('change_password'))
    return render_template('change_password.html', form=form)

@app.route('/admin/users')
@login_required
def list_users():
    if not current_user.is_admin:
        flash('您没有权限访问此页面。', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.args.get('export') == 'csv':
        users = User.query.all()
        usernames = [user.username for user in users]
        count_data = db.session.query(
            CheckInRecord.user_id,
            func.count(CheckInRecord.id)
        ).filter(CheckInRecord.user_id.in_(usernames)) \
            .group_by(CheckInRecord.user_id).all()
        checkin_counts = {user_id: count for user_id, count in count_data}
        
        # 写入 CSV 数据
        si = io.StringIO()
        cw = csv.writer(si)
        cw.writerow(['学号', '姓名', '学院', 'QQ', '签到次数'])
        for user in users:
            sign_count = checkin_counts.get(user.username, 0)
            cw.writerow([user.username, user.name, user.Departments, user.QQ, sign_count])
        output = si.getvalue()
        si.close()
        headers = {
            "Content-Disposition": "attachment; filename=users.csv",
            "Content-type": "text/csv"
        }
        return Response(output, headers=headers)


    # users = User.query.all()
    page = request.args.get('page', 1, type=int)
    per_page = 20
    pagination = User.query.paginate(page=page, per_page=per_page, error_out=False)
    users = pagination.items
    usernames = [user.username for user in users]
    count_data = db.session.query(
        CheckInRecord.user_id,
        func.count(CheckInRecord.id)
    ).filter(CheckInRecord.user_id.in_(usernames)) \
     .group_by(CheckInRecord.user_id).all()
    checkin_counts = {user_id: count for user_id, count in count_data}
    
    return render_template('usersTable.html', users=users, pagination=pagination, checkin_counts=checkin_counts)

@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        flash('您没有权限执行此操作。', 'danger')
        return redirect(url_for('dashboard'))
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('用户已删除。', 'success')
    return redirect(url_for('list_users'))

@app.route('/admin/users/edit/<int:user_id>/<field>', methods=['GET', 'POST'])
@login_required
def edit_user_field(user_id, field):
    if not current_user.is_admin:
        flash('您没有权限执行此操作。', 'danger')
        return redirect(url_for('dashboard'))
    user = User.query.get_or_404(user_id)
    valid_fields = {
        'QQ': 'QQ',
        'Name': 'name',
        'Dep': 'Departments'
    }
    if field not in valid_fields:
        abort(404)
    if request.method == 'POST':
        user.username = request.form['username']
        setattr(user, valid_fields[field], request.form['value'])
        db.session.commit()
        flash('用户信息已更新。', 'success')
        return redirect(url_for('list_users'))
    return render_template('editUser.html', user=user, lab=field, value=getattr(user, valid_fields[field]))

@app.route('/admin/user/<username>/records')
@login_required
def user_checkin_records(username):
    if not current_user.is_admin:
        flash('您没有权限访问此页面。', 'danger')
        return redirect(url_for('dashboard'))
    user = User.query.filter_by(username=username).first_or_404()
    records = CheckInRecord.query.filter_by(user_id=username).order_by(CheckInRecord.date.desc()).all()
    record_previews = []
    for record in records:
        try:
            with open(record.file_path, encoding='utf-8') as f:
                preview = f.read(100)
        except Exception:
            preview = '[读取失败]'
        record_previews.append({
            'date': record.date,
            'file_path': record.file_path,
            'preview': preview
        })
            # CSV 导出功能：检测是否带上 export=csv 参数

    total = len(records)
    return render_template('admin_user_records.html', user=user, records=record_previews, total=total)

# ----------------管理打卡时间段及例外日期----------------

# 列出所有打卡时间段（管理员）
@app.route('/admin/sign_periods')
@login_required
def list_sign_periods():
    if not current_user.is_admin:
        flash('您没有权限访问此页面。', 'danger')
        return redirect(url_for('dashboard'))
    periods = SignPeriod.query.order_by(SignPeriod.start_date.desc()).all()
    return render_template('admin_sign_periods.html', periods=periods)

# 新增打卡时间段（管理员）
@app.route('/admin/sign_periods/add', methods=['GET', 'POST'])
@login_required
def add_sign_period():
    if not current_user.is_admin:
        flash('您没有权限访问此页面。', 'danger')
        return redirect(url_for('dashboard'))
    form = SignPeriodForm()
    if form.validate_on_submit():
        new_period = SignPeriod(
            name=form.name.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data
        )
        db.session.add(new_period)
        db.session.commit()
        flash('打卡时间段添加成功。', 'success')
        return redirect(url_for('list_sign_periods'))
    return render_template('admin_add_sign_period.html', form=form)

# 管理某个时间段的例外日期（管理员）
@app.route('/admin/sign_periods/<int:period_id>/exceptions', methods=['GET', 'POST'])
@login_required
def manage_exceptions(period_id):
    if not current_user.is_admin:
        flash('您没有权限访问此页面。', 'danger')
        return redirect(url_for('dashboard'))
    period = SignPeriod.query.get_or_404(period_id)
    form = ExceptionDateForm()
    if form.validate_on_submit():
        # 添加新的例外日期
        new_exception = SignInException(
            period_id=period.id,
            exception_date=form.exception_date.data
        )
        db.session.add(new_exception)
        db.session.commit()
        flash('休息日期添加成功。', 'success')
        return redirect(url_for('manage_exceptions', period_id=period.id))
    exceptions = period.exceptions
    return render_template('admin_manage_exceptions.html', period=period, exceptions=exceptions, form=form)

# 按时间段查看全部打卡记录（管理员）
@app.route('/admin/records_by_period/<int:period_id>')
@login_required
def records_by_period(period_id):
    if not current_user.is_admin:
        flash('您没有权限访问此页面。', 'danger')
        return redirect(url_for('dashboard'))

    period = SignPeriod.query.get_or_404(period_id)
    # 构造查询，统计每个用户在指定周期内的签到次数
    query = db.session.query(
                User,
                func.count(CheckInRecord.id).label('sign_count')
            ) \
            .outerjoin(
                CheckInRecord,
                and_(
                    User.username == CheckInRecord.user_id,
                    func.date(CheckInRecord.date) >= func.date(period.start_date),
                    func.date(CheckInRecord.date) <= func.date(period.end_date)
                )
            ) \
            .group_by(User.id) \
            .order_by(User.id)

    # 若需要导出 CSV，则获取全部数据，不进行分页处理
    if request.args.get('export') == 'csv':
        records = query.all()
        si = io.StringIO()
        cw = csv.writer(si)
        cw.writerow(['学号', '姓名', '学院', '签到次数'])
        for user, sign_count in records:
            cw.writerow([user.username, user.name, user.Departments, sign_count])
        output = si.getvalue()
        si.close()
        headers = {
            "Content-Disposition": f"attachment; filename=records_period_{period.id}.csv",
            "Content-type": "text/csv"
        }
        return Response(output, headers=headers)

    # # 分页功能：每页最多20条记录，导出时不受此影响
    # page = request.args.get('page', 1, type=int)
    # per_page = 20
    # # 获取全部记录用于分页（数据量不大时可接受，如数据量较大建议使用数据库级分页）
    # all_records = query.all()
    # total = len(all_records)
    # start = (page - 1) * per_page
    # end = start + per_page
    # records_page = all_records[start:end]
    # # total_pages = (total + per_page - 1) // per_page

    page = request.args.get('page', 1, type=int)
    per_page = 20
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    records = pagination.items



    return render_template(
        'admin_records_by_period.html',
        period=period,
        records=records,
        page=page,
        per_page=per_page,
        # total=total,
        pagination=pagination
    )

# 程序入口
if __name__ == '__main__':
    # 初次运行时请解除下面两行注释以创建数据库表
    # with app.app_context():
    #     db.create_all()
    app.run(host='0.0.0.0',port=5001, debug=True)
