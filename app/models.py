from datetime import datetime
from hashlib import md5
from time import time
from flask import current_app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from app import db, login


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(128), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    about_me = db.Column(db.String(128))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    groups = db.relationship("Group", secondary="group_member", backref=db.backref("users", lazy=True,cascade="all, delete, delete-orphan", passive_deletes=True, single_parent=True))
    membership_requests = db.relationship("MembershipRequest", cascade="all, delete, delete-orphan", passive_deletes=True, single_parent=True, backref=db.backref("user", lazy=True))
    invitations = db.relationship("Invitation",cascade="all, delete, delete-orphan", passive_deletes=True, single_parent=True, backref=db.backref("user", lazy=True))

    def __repr__(self):
        return f"User - username:{self.username}, email:{self.email}"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode("utf-8")).hexdigest()
        return f"https://avatars.dicebear.com/api/personas/{digest}.svg?size={size}"

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {"reset_password": self.id, "exp": time() + expires_in},
            current_app.config["SECRET_KEY"],
            algorithm="HS256",
        )

    def date_joined(self, group):
        Membership = GroupMember.query.filter_by(user_id=self.id, group_id=group.id).first_or_404()
        return Membership.date_added

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])[
                "reset_password"
            ]
        except:
            return
        return User.query.get(id)

    def is_invited(self, group):
        return Invitation.query.filter_by(user_id=self.id, group_id=group.id).first() is not None

    def get_invitation(self,group):
        if self.is_invited(group):
            return Invitation.query.filter_by(user_id=self.id, group_id=group.id).first()
        return None

    def has_asked_for_membership(self, group):
        return MembershipRequest.query.filter_by(user_id=self.id, group_id=group.id).first() is not None

    def get_membership_request(self,group):
        if self.has_asked_for_membership(group):
            return MembershipRequest.query.filter_by(user_id=self.id, group_id=group.id).first()
        return None


    def get_user_debts(self):
        user_as_expense_member = (
            db.session.query(ExpenseMember)
            .join(GroupMember)
            .filter(GroupMember.user_id == self.id, ExpenseMember.has_paid == False)
            .all()
        )
        return user_as_expense_member

    def get_user_pending_debts(self):
        user_as_expense_member = self.get_user_debts()
        list_of_expenses = [expense_member.expense_id for expense_member in user_as_expense_member]
        expenses = Expense.query.filter(Expense.id.in_(list_of_expenses))
        return expenses

    def get_user_expenses(self):
        user_as_lender = (
            db.session.query(Expense)
            .join(GroupMember)
            .filter(GroupMember.user_id == self.id, Expense.is_paid == False)
        )
        return user_as_lender

    def get_amount_of_user_debts(self):
        debts = self.get_user_debts()
        total_debt = 0
        for debt in debts:
            total_debt += debt.amount_borrowed
        users_debts = self.get_user_pending_debts()
        for debt in users_debts:
            total_debt -= debt.get_amount_paid(self)
        return total_debt

    def get_amount_of_payed_expenses(self):
        expenses = self.get_user_expenses()
        total_payed_for = 0
        for expense in expenses:
            total_payed_for += expense.get_amount_owed()
            members = expense.get_members()
            for member in members:
                user = (
                db.session.query(User)
                .join(GroupMember, GroupMember.user_id == User.id)
                .filter(GroupMember.id == member.group_member_id)
                .first()
                )
                total_payed_for -= expense.get_amount_paid(user)
        return total_payed_for

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete='CASCADE'))
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.String(128))
    owner = db.relationship("User", foreign_keys=[owner_id], backref=db.backref("owned_groups", lazy=True, cascade="all, delete, delete-orphan", passive_deletes=True, single_parent=True))
    membership_requests = db.relationship("MembershipRequest", cascade="all, delete, delete-orphan", passive_deletes=True, single_parent=True, backref=db.backref("group", lazy=True))
    invitations = db.relationship("Invitation", cascade="all, delete, delete-orphan", passive_deletes=True, single_parent=True,  backref=db.backref("group", lazy=True))

    def add_to_group(self, user):
        if not self.is_member(user):
            self.users.append(user)

    def remove_from_group(self, user):
        if self.is_member(user):
            self.users.remove(user)

    def is_member(self, user):
        return user in self.users

    def avatar(self, size):
        digest = md5(self.description.lower().encode("utf-8")).hexdigest()
        return f"https://avatars.dicebear.com/api/identicon/{digest}.svg?size={size}"


class GroupMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("group.id", ondelete='CASCADE'))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete='CASCADE'))
    date_added = db.Column(db.DateTime, default=datetime.utcnow)


class MembershipRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("group.id", ondelete='CASCADE'))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete='CASCADE'))
    request_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(64), nullable=False)

    def cancel_request(self):
        self.status = 'cancelled'

    def accept_request(self, user):
        self.status = 'accepted'
        self.group.add_to_group(user)

    def decline_request(self):
        self.status = 'declined'



class Invitation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("group.id", ondelete='CASCADE'))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete='CASCADE'))
    invitation_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(64), nullable=False)

    def accept_invitation(self, user):
        self.status = 'accepted'
        self.group.add_to_group(user)

    def decline_invitation(self):
        self.status = 'declined'

    def cancel_invitation(self):
        self.status = 'cancelled'


class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64), unique=True, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(128))
    lender_id = db.Column(db.Integer, db.ForeignKey("group_member.id",ondelete='CASCADE'))
    group_id = db.Column(db.Integer, db.ForeignKey("group.id",ondelete='CASCADE'))
    is_paid = db.Column(db.Boolean, default=False)
    added_on = db.Column(db.DateTime, default=datetime.utcnow)
    members = db.relationship("GroupMember", secondary="expense_member", backref=db.backref("expenses", lazy=True))
    lender = db.relationship("GroupMember", foreign_keys=[lender_id], backref=db.backref("lended_expenses", lazy=True))
    group = db.relationship("Group", foreign_keys=[group_id], backref=db.backref("expenses", lazy=True))

    def add_members(self, members_list_ids):
        members_list = GroupMember.query.filter(GroupMember.user_id.in_(members_list_ids), GroupMember.group_id == self.group_id).all()
        print([member.user_id for member in members_list])
        for member in members_list:
            self.members.append(member)
        db.session.commit()

    def set_amount_borrowed(self):
        borrowed = self.amount / (len(self.members) + 1)
        group_members_ids = [group_member.id for group_member in self.members]
        members_list = ExpenseMember.query.filter(ExpenseMember.group_member_id.in_(group_members_ids), ExpenseMember.expense_id == self.id, GroupMember.group_id == self.group_id).all()
        for member in members_list:
            member.amount_borrowed = borrowed
        db.session.commit()

    def get_amount_paid(self, user):
        expense_member = (
            db.session.query(ExpenseMember)
            .join(GroupMember, GroupMember.id == ExpenseMember.group_member_id)
            .join(User, User.id == GroupMember.user_id)
            .join(Expense, Expense.id == ExpenseMember.expense_id)
            .filter(User.id == user.id, Expense.id == self.id)
            .first())
        amount_paid = 0
        for transaction in expense_member.member_transactions:
            amount_paid += transaction.amount
        return amount_paid

    def get_amount_needs_to_seddle(self, user):
        expense_member = (
            db.session.query(ExpenseMember)
            .join(GroupMember, GroupMember.id == ExpenseMember.group_member_id)
            .join(User, User.id == GroupMember.user_id)
            .join(Expense, Expense.id == ExpenseMember.expense_id)
            .filter(User.id == user.id, Expense.id == self.id)
            .first())
        return expense_member.amount_borrowed

    def get_lender_name(self):
        user_id = db.session.query(GroupMember.user_id).filter(GroupMember.id == self.lender_id).scalar()
        user = User.query.filter_by(id=user_id).first()
        return user.username

    def get_group_name(self):
        group = (
            db.session.query(Group)
            .join(Expense, Expense.group_id == Group.id)
            .filter(Expense.id == self.id)
            .first()
        )
        return group.name

    def get_members(self):
        return ExpenseMember.query.filter_by(expense_id=self.id).all()

    def get_member_names(self):
        names = []
        for member in self.members:
            names.append(
                db.session.query(User.username)
                .join(GroupMember, GroupMember.user_id == User.id)
                .filter(GroupMember.id == member.id)
                .scalar()
            )
        return names

    def get_amount_owed(self):
        return (self.amount / (len(self.members) + 1)) * (len(self.members))



class ExpenseMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    expense_id = db.Column(db.Integer, db.ForeignKey("expense.id", ondelete='CASCADE'))
    group_member_id = db.Column(db.Integer, db.ForeignKey("group_member.id", ondelete='CASCADE'))
    has_paid = db.Column(db.Boolean, default=False)
    amount_borrowed = db.Column(db.Float)

    def get_name(self):
        group_member = GroupMember.query.filter_by(id=self.group_member_id).first()
        user = User.query.filter_by(id=group_member.user_id).first()
        return user.username


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    expense_id = db.Column(db.Integer, db.ForeignKey("expense.id", ondelete='CASCADE'))
    expense_member_id = db.Column(db.Integer, db.ForeignKey("expense_member.id", ondelete='CASCADE'))
    amount = db.Column(db.Float)
    note = db.Column(db.String(128))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    expense = db.relationship("Expense", foreign_keys=[expense_id], backref=db.backref("transactions", lazy=True))
    expense_member = db.relationship("ExpenseMember", foreign_keys=[expense_member_id], backref=db.backref("member_transactions", lazy=True))