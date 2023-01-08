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
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
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

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete='CASCADE'))
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.String(255))
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
    membership_status = db.Column(db.String(255))



class MembershipRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("group.id", ondelete='CASCADE'))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete='CASCADE'))
    request_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(255))

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
    status = db.Column(db.String(255))

    def accept_invitation(self, user):
        self.status = 'accepted'
        self.group.add_to_group(user)

    def decline_invitation(self):
        self.status = 'declined'

    def cancel_invitation(self):
        self.status = 'cancelled'