from flask_wtf import FlaskForm
from wtforms import StringField,SubmitField,PasswordField
from wtforms.validators import DataRequired,URL,Email
from flask_ckeditor import CKEditorField
import email_validator



class CreateBlog(FlaskForm):
    title=StringField(label="Title of Blog",validators=[DataRequired()])
    subtitle=StringField(label="Subtitle",validators=[DataRequired()])
    img_url=StringField(label="Blog Image URL",validators=[DataRequired(),URL()])
    body=CKEditorField(label="Blog Content",validators=[DataRequired()])
    submit=SubmitField("Submit Post")


class RegisterForm(FlaskForm):
    email=StringField(label="Email",validators=[DataRequired(),Email(granular_message=True)])
    name=StringField(label="Name",validators=[DataRequired()])
    password=PasswordField(label="Password",validators=[DataRequired()])
    submit=SubmitField(label="Sign Up")


class LoginForm(FlaskForm):
    email=StringField(label="Email",validators=[DataRequired(),Email()])
    password=PasswordField(label="Password",validators=[DataRequired()])
    
class CommentForm(FlaskForm):
    comment_text=CKEditorField(label="Comment",validators=[DataRequired()])
    submit=SubmitField("Submit Comment")