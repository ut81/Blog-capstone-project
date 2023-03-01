from flask import Flask,render_template,request,redirect,url_for,flash,abort
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin,LoginManager,login_user,logout_user,current_user,login_required
from flask_ckeditor import CKEditor
from forms import CreateBlog,RegisterForm,LoginForm,CommentForm
from werkzeug.security import generate_password_hash,check_password_hash
from datetime import date
from functools import wraps
from sqlalchemy.orm import relationship
from flask_gravatar import Gravatar
import smtplib

app=Flask(__name__)
app.config['SECRET_KEY']="8BYkEfBA6O6donzWlSihBXox7C0sKR6b"
ckeditor=CKEditor(app)
Bootstrap(app)
##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI']="sqlite:///posts.db"
db=SQLAlchemy(app)


gravatar = Gravatar(app, size=100, rating='g', default='retro', force_default=False, force_lower=False, use_ssl=False, base_url=None)




## LOGIN USER

login_manager=LoginManager()
login_manager.init_app(app)



class User(UserMixin,db.Model):
    __tablename__="users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))
    posts = relationship("Blogpost", back_populates="author")
    comments = relationship("Comment", back_populates="comment_author")



## CREATE CLASS
class Blogpost(db.Model):
    __tablename__="blog-posts"
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = relationship("User", back_populates="posts")
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    comments = relationship("Comment", back_populates="parent_post")


class Comment(db.Model):
    __tablename__="comments"
    id=db.Column(db.Integer,primary_key=True)
    post_id=db.Column(db.Integer,db.ForeignKey("blog-posts.id"))
    author_id=db.Column(db.Integer,db.ForeignKey("users.id"))
    parent_post=relationship("Blogpost",back_populates="comments")
    comment_author=relationship("User",back_populates="comments")
    text = db.Column(db.Text, nullable=False)
    date = db.Column(db.String(250), nullable=False)




with app.app_context():
    db.create_all()


def admin_only(f):
    @wraps(f)
    def decorated_function(*args,**kwargs):
        if current_user.id!=1:
            return abort(403)
        return f(*args,**kwargs)
    return decorated_function



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def home():
    data=Blogpost.query.all()
    return render_template("index.html",posts=data,current_user=current_user,logged_in=current_user.is_authenticated)


@app.route('/about')
def about():
    return render_template("about.html",logged_in=True)


@app.route('/blog/<int:index>',methods=['GET','POST'])
def post(index):
    form=CommentForm()
    requested_post=Blogpost.query.get(index)
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to login or register to comment")
            return redirect(url_for('login'))


        new_comment=Comment(
            text=form.comment_text.data,
            comment_author=current_user,
            parent_post=requested_post,
            date=date.today().strftime("%B %d,%Y")
        )
        db.session.add(new_comment)
        db.session.commit()
    return render_template("post.html",form=form,post=requested_post,logged_in=current_user.is_authenticated)






    


@app.route('/add-post',methods=['GET','POST'])
@login_required
@admin_only
def new_post():
    form=CreateBlog()
    if request.method=='POST':
        if form.validate_on_submit:
            with app.app_context():
                new_post=Blogpost(
                    title=form.title.data,
                    subtitle=form.subtitle.data,
                    body=form.body.data,
                    date=date.today().strftime("%B %d,%Y"),
                    author=current_user,
                    img_url=form.img_url.data

                )
                db.session.add(new_post)
                db.session.commit()
                return redirect(url_for('home'))

    return render_template("make-post.html",form=form,logged_in=True)



@app.route('/edit-post/<int:post_id>',methods=["GET","POST"])
@login_required
@admin_only
def edit_post(post_id):
    post=Blogpost.query.get(post_id)
    edit_form=CreateBlog(
        title=post.title,
        body=post.body,
        img_url=post.img_url,
        author=post.author,
        subtitle=post.subtitle

    )

    if edit_form.validate_on_submit():
               
        post.title=edit_form.title.data
        post.body=edit_form.body.data
        post.img_url=edit_form.img_url.data
        post.author=edit_form.author.data
        post.subtitle=edit_form.subtitle.data
        db.session.commit()
        return redirect(url_for('post',index=post.id))
    return render_template("make-post.html",is_edit=True,form=edit_form)


@app.route("/delete-post/<int:post_id>")
@login_required
@admin_only
def delete_post(post_id):
    post=Blogpost.query.get(post_id)
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('home'))



@app.route('/sign-up',methods=['GET','POST'])
def register():
    form=RegisterForm()
    if request.method=='POST':
       if form.validate_on_submit():

        if User.query.filter_by(email=form.email.data).first():
            flash("you've already signed up with that email,login instead!!")
            return redirect(url_for('login'))

        with app.app_context():

            new_user=User(
        
            name=form.name.data,
            email=form.email.data,
            password=generate_password_hash(form.password.data,method="pbkdf2:sha256",salt_length=8)
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        
        return redirect(url_for('home'))

    return render_template('register.html',form=form)


@app.route('/login',methods=['GET','POST'])
def login():
    form=LoginForm()
    if form.validate_on_submit():

        email=form.email.data
        password=form.password.data
        user=User.query.filter_by(email=email).first()
        if not user:
            flash("This email doesn't exist, Please try again!!")
            return redirect(url_for('login'))

        elif not check_password_hash(user.password,password):
            flash("Password incorrect, Please try again!!")
            return redirect(url_for('login'))

        else:
            login_user(user)
            print(current_user.name)
            return redirect(url_for('home',logged_in=True))   

    return render_template('login.html',form=form)
@app.route('/contact',methods=['GET','POST'])
@login_required
def contact():
    if request.method=='POST':
        data=request.form
        with smtplib.SMTP("smtp.gmail.com") as connection:
            connection.starttls()
            connection.login("your_email","your_password")
            connection.sendmail("your_email","your_email",msg=f"Subject:new Message \n\n Name: {data['name']}\nEmail: {data['email']}\nPhone: {data['phone']}\nMessage:{data['message']} ")
        return render_template("contact.html",msg_sent=True,logged_in=True)
    
    return render_template("contact.html",logged_in=True)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))
    
if __name__=="__main__":

    app.run(debug=True)