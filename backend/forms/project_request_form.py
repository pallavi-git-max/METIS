from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length

class ProjectRequestForm(FlaskForm):
    project_title = StringField('Project Title', validators=[DataRequired(), Length(max=255)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(max=2000)])
    submit = SubmitField('Submit Request')
