from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectMultipleField
from wtforms.validators import DataRequired, Length, ValidationError
from app.models import User, Group, Invitation

class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    about_me = TextAreaField('About me', validators=[Length(min=0, max=140)])
    submit = SubmitField('Submit')

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError('Please use a different username.')

class CreateGroup(FlaskForm):
    group_name = StringField('Group name', validators=[DataRequired()])
    description = StringField('Group description', validators=[DataRequired(), Length(min=0, max=140)])
    members = SelectMultipleField('Members', coerce=int)
    submit = SubmitField('Create')

    def __init__(self, owner_id, *args, **kwargs):
        super(CreateGroup, self).__init__(*args, **kwargs)
        self.members.choices = [(user.id, user.username) for user in User.query.filter(User.id!=owner_id)]

    def validate_group_name(self, group_name):
        group = Group.query.filter_by(name=group_name.data).first()
        if group is not None:
            raise ValidationError('Please use a different username.')

class EditGroup(FlaskForm):
    group_name = StringField('Group name', validators=[DataRequired()])
    description = StringField('Group description', validators=[DataRequired(), Length(min=0, max=140)])
    members = SelectMultipleField('Invite new members', coerce=int)
    submit = SubmitField('Update')

    def __init__(self, group_id, *args, **kwargs):
        super(EditGroup, self).__init__(*args, **kwargs)
        current_members = Group.query.filter_by(id=group_id).first().users
        invitations_to_group = Group.query.filter_by(id=group_id).first().invitations
        requests_to_group = Group.query.filter_by(id=group_id).first().membership_requests
        curr_member_ids = [member.id for member in current_members]
        invited_members_ids = [inv.user_id for inv in invitations_to_group]
        requested_members_ids = [inv.user_id for inv in requests_to_group]
        list_of_ids_to_filter_out = curr_member_ids + invited_members_ids + requested_members_ids
        self.members.choices = [(user.id, user.username) for user in User.query.filter(User.id.not_in(list_of_ids_to_filter_out))]
        self.original_name = Group.query.filter_by(id=group_id).first().name

    def validate_group_name(self, group_name):
        if group_name.data != self.original_name:
            group = Group.query.filter_by(name=self.group_name.data).first()
            if group is not None:
                raise ValidationError('Please use a different groupname.')





