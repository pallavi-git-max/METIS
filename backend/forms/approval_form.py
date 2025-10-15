from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField, BooleanField
from wtforms.validators import DataRequired

class ApprovalForm(FlaskForm):
    approved = BooleanField('Approve')
    comments = TextAreaField('Comments')
    submit = SubmitField('Submit')
