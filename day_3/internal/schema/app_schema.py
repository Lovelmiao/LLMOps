

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length

class CompletionForm(FlaskForm):
    user_input = StringField('user_input', validators=[DataRequired(message="用户输入必须填写"), Length(min=1, max=500, message="用户输入长度必须在1到500之间")])
