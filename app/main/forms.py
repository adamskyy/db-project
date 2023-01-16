from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectMultipleField, SelectField, FloatField, DateField
from wtforms.validators import DataRequired, Length, ValidationError, NumberRange
from app.models import User, Group, GroupMember, Expense

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
        self.members.choices = [(user.id, user.username) for user in User.query.filter(User.id != owner_id, User.is_admin == False)]

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
        self.members.choices = [(user.id, user.username) for user in User.query.filter(User.id.not_in(list_of_ids_to_filter_out), User.is_admin == 0)]
        self.original_name = Group.query.filter_by(id=group_id).first().name

    def validate_group_name(self, group_name):
        if group_name.data != self.original_name:
            group = Group.query.filter_by(name=self.group_name.data).first()
            if group is not None:
                raise ValidationError('Please use a different groupname.')


class CreateExpense(FlaskForm):
    title = StringField('Expense title', validators=[DataRequired()])
    amount = FloatField('Amount of money paid', validators=[DataRequired(), NumberRange(min=1, message="The value should be minimal 1$.")])
    description = StringField('Expense description', validators=[DataRequired(), Length(min=0, max=140)])
    members = SelectMultipleField('Split with', coerce=int)
    submit = SubmitField('Create')

    def __init__(self, group_id, self_id, *args, **kwargs):
        super(CreateExpense, self).__init__(*args, **kwargs)
        self.members.choices = [(user.id, user.username) for member in GroupMember.query.filter(GroupMember.group_id == group_id, GroupMember.user_id != self_id).all() for user in User.query.filter_by(id=member.user_id).all()]


class CreateTransaction(FlaskForm):
    amount = FloatField('Register transaction with amount:', validators=[DataRequired(), NumberRange(min=1, message="The value should be minimal 1$.")])
    note = StringField('Transaction description', validators=[DataRequired(), Length(min=0, max=140)])
    date = DateField('Paid on', validators=[DataRequired()])
    submit = SubmitField('Register transaction')
    already_paid = 0
    need_to_pay = 0

    def __init__(self, expense_id, user, *args, **kwargs):
        super(CreateTransaction, self).__init__(*args, **kwargs)
        expense = Expense.query.filter_by(id=expense_id).first_or_404()
        self.already_paid = expense.get_amount_paid(user)
        self.need_to_pay = expense.get_amount_needs_to_seddle(user)


    def validate_amount(self, amount):
        print(self.need_to_pay - self.already_paid)
        if amount.data > (self.need_to_pay - self.already_paid):
            raise ValidationError('You paid too much!')