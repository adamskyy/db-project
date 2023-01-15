from app.main import bp
from flask import render_template, flash, redirect, url_for, request, abort
from flask_login import current_user, login_required
from datetime import datetime
from app import db
from app.models import User, Group, Invitation, MembershipRequest, GroupMember, Expense, ExpenseMember, Transaction
from app.main.forms import EditProfileForm, CreateGroup, EditGroup, CreateExpense, CreateTransaction


@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

@bp.route('/', methods=['GET'])
@bp.route('/index', methods=['GET'])
def index():
    if current_user.is_authenticated:
        page_group = request.args.get('page_group', 1, type=int)
        page_debt = request.args.get('page_debt', 1, type=int)
        page_expense = request.args.get('page_expense', 1, type=int)
        groups = Group.query.filter(Group.id.in_([g.id for g in current_user.groups])).paginate(page=page_group, per_page=3)
        debts = current_user.get_user_pending_debts().paginate(page=page_debt, per_page=2)
        expenses = current_user.get_user_expenses().paginate(page=page_expense, per_page=2)
        return render_template('index.html', title='index', groups=groups, debts=debts, expenses=expenses)

    return render_template('index.html', title='index')

@bp.route('/user/<username>', methods=['GET'])
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    if current_user.username == username:
        page_group = request.args.get('page_group', 1, type=int)
        page_invitation = request.args.get('page_invitation', 1, type=int)
        page_request = request.args.get('page_request', 1, type=int)
        groups_id = [group.id for group in user.groups]
        groups = Group.query.filter(Group.id.in_(groups_id)).paginate(page=page_group, per_page=1)
        invitations = Invitation.query.filter_by(user_id=user.id).paginate(page=page_invitation, per_page=1)
        requests = MembershipRequest.query.filter_by(user_id=user.id).paginate(page=page_request, per_page=1)
        return render_template('user.html', title='User page', user=user, groups=groups, invitations=invitations, requests=requests)
    users_groups_id = [group.id for group in user.groups]
    common_groups_id = [group.id for group in current_user.groups if group.id in users_groups_id]
    page_common_group = request.args.get('page_common_group', 1, type=int)
    common_groups = Group.query.filter(Group.id.in_(common_groups_id)).paginate(page=page_common_group, per_page=1)
    return render_template('user.html', title='User page', user=user, common_groups=common_groups)

@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes in your profile have been saved.', 'success')
        return redirect(url_for('main.index'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile', form=form)


@bp.route('/create_group', methods=['GET', 'POST'])
@login_required
def create_group():
    form = CreateGroup(current_user.id)
    if form.validate_on_submit():
        group = Group(name=form.group_name.data, owner_id=current_user.id, description=form.description.data)
        db.session.add(group)
        db.session.commit()
        group.add_to_group(current_user)
        for form_user_id in form.members.data:
            invitation = Invitation(group_id=group.id, user_id=form_user_id, status='pending')
            db.session.add(invitation)
            db.session.commit()
        flash('Your group has been created.', 'success')
        return redirect(url_for('main.index'))
    return render_template('create_group.html', title='Edit Profile', form=form)


@bp.route('/invitation/<invitation_id>/accept', methods=['POST'])
def accept_invitation(invitation_id):
    invitation = Invitation.query.filter_by(id=invitation_id).first_or_404()
    invitation.accept_invitation(invitation.user)
    db.session.commit()
    return redirect(url_for('main.index'))


@bp.route('/invitation/<invitation_id>/decline', methods=['POST'])
def decline_invitation(invitation_id):
    invitation = Invitation.query.filter_by(id=invitation_id).first_or_404()
    invitation.decline_invitation()
    db.session.commit()
    return redirect(url_for('main.index'))


@bp.route('/group/<groupname>', methods=['GET'])
@login_required
def group(groupname):
    group = Group.query.filter_by(name=groupname).first_or_404()
    page_expense = request.args.get('page_expense', 1, type=int)
    group_expenses = Expense.query.filter(Expense.group_id == group.id).paginate(page=page_expense, per_page=1)
    if current_user.id == group.owner.id:
        page_user = request.args.get('page_user', 1, type=int)
        page_request = request.args.get('page_request', 1, type=int)
        page_invitation = request.args.get('page_invitation', 1, type=int)
        users_id = [user.id for user in group.users]
        group_users = User.query.filter(User.id.in_(users_id)).paginate(page=page_user, per_page=1)
        group_requests = MembershipRequest.query.filter_by(group_id=group.id).paginate(page=page_request, per_page=1)
        group_invitations = Invitation.query.filter_by(group_id=group.id).paginate(page=page_invitation, per_page=1)
        return render_template('group_admin.html', title='Group page', group=group, group_requests=group_requests, group_users=group_users, group_invitations=group_invitations, group_expenses=group_expenses)
    page_user = request.args.get('page_user', 1, type=int)
    users_id = [user.id for user in group.users]
    group_users = User.query.filter(User.id.in_(users_id)).paginate(page=page_user, per_page=1)
    return render_template('group.html', title='Group page', group=group, group_users=group_users, group_expenses=group_expenses)


@bp.route('/remove_user/<group_id>/<user_id>', methods=['GET', 'POST'])
@login_required
def remove_user(group_id, user_id):
    group = Group.query.filter_by(id=group_id).first_or_404()
    user = User.query.filter_by(id=user_id).first_or_404()
    prev_Invitation = Invitation.query.filter_by(group_id=group_id, user_id=current_user.id).first()
    prev_Memb_requests = MembershipRequest.query.filter_by(group_id=group_id, user_id=current_user.id).first()
    # check if current user is admin of the group
    if current_user.id == group.owner.id:
        if prev_Invitation is not None:
            db.session.delete(prev_Invitation)
        if prev_Memb_requests is not None:
            db.session.delete(prev_Memb_requests)
        group.remove_from_group(user)
        db.session.commit()
    else:
        return abort(403)
    return redirect(url_for('main.group', groupname=group.name))


@bp.route('/edit_group/<group_id>', methods=['GET', 'POST'])
@login_required
def edit_group(group_id):
    group = Group.query.filter_by(id=group_id).first_or_404()
    form = EditGroup(group_id)
    if form.validate_on_submit():
        group.name = form.group_name.data
        group.description = form.description.data
        for form_user_id in form.members.data:
            invitation = Invitation(group_id=group.id, user_id=form_user_id, status='pending')
            db.session.add(invitation)
            db.session.commit()
        flash('Your changes in your group have been saved.', 'success')
        return redirect(url_for('main.group', groupname=group.name))
    elif request.method == 'GET':
        form.group_name.data = group.name
        form.description.data = group.description
    return render_template('edit_group.html', title='Edit Group', form=form, group=group)


@bp.route('/request_membership/<group_id>', methods=['POST'])
@login_required
def request_membership(group_id):
    membershipRequest = MembershipRequest(group_id=group_id, user_id=current_user.id, status="pending")
    db.session.add(membershipRequest)
    db.session.commit()
    group = Group.query.filter_by(id=group_id).first_or_404()
    return redirect(url_for('main.group', groupname=group.name))


@bp.route('/cancel_membership_request/<request_id>', methods=['POST'])
@login_required
def cancel_membership_request(request_id):
    membershipRequest = MembershipRequest.query.filter_by(id=request_id).first_or_404()
    membershipRequest.status = 'cancelled'
    db.session.commit()
    group = Group.query.filter_by(id=membershipRequest.group_id).first_or_404()
    return redirect(url_for('main.group', groupname=group.name))

@bp.route('/discard_membership_request/<request_id>', methods=['POST'])
@login_required
def discard_membership_request(request_id):
    membershipRequest = MembershipRequest.query.filter_by(id=request_id).first()
    group_name = Group.query.filter_by(id=membershipRequest.group_id).first_or_404().name
    db.session.delete(membershipRequest)
    db.session.commit()
    return redirect(url_for('main.group', groupname=group_name))

@bp.route('/quit_from_group/<group_id>', methods=['POST'])
@login_required
def quit_from_group(group_id):
    group_name = Group.query.filter_by(id=group_id).first_or_404().name
    groupMember = GroupMember.query.filter_by(group_id=group_id, user_id=current_user.id).first_or_404()
    prev_Invitation = Invitation.query.filter_by(group_id=group_id, user_id=current_user.id).first()
    prev_Memb_requests = MembershipRequest.query.filter_by(group_id=group_id, user_id=current_user.id).first()
    db.session.delete(groupMember)
    if prev_Invitation is not None:
        db.session.delete(prev_Invitation)
    if prev_Memb_requests is not None:
        db.session.delete(prev_Memb_requests)
    db.session.commit()
    return redirect(url_for('main.group', groupname=group_name))

@bp.route('/cancel_invitation/<invitation_id>', methods=['POST'])
@login_required
def cancel_invitation(invitation_id):
    invitation = Invitation.query.filter_by(id=invitation_id).first_or_404()
    invitation.cancel_invitation()
    db.session.commit()
    return redirect(url_for('main.group', groupname=invitation.group.name))


@bp.route('/remove_invitation/<invitation_id>', methods=['POST'])
@login_required
def remove_invitation(invitation_id):
    invitation = Invitation.query.filter_by(id=invitation_id).first_or_404()
    groupname = invitation.group.name
    db.session.delete(invitation)
    db.session.commit()
    return redirect(url_for('main.group', groupname=groupname))


@bp.route('/accept_request/<request_id>', methods=['POST'])
@login_required
def accept_request(request_id):
    request = MembershipRequest.query.filter_by(id=request_id).first_or_404()
    request.accept_request(request.user)
    db.session.commit()
    return redirect(url_for('main.group', groupname=request.group.name))


@bp.route('/decline_request/<request_id>', methods=['POST'])
@login_required
def decline_request(request_id):
    request = MembershipRequest.query.filter_by(id=request_id).first_or_404()
    request.decline_request(request.user)
    db.session.commit()
    return redirect(url_for('main.group', groupname=request.group.name))


@bp.route('/quit/<group_id>', methods=['POST'])
@login_required
def quit_group(group_id):
    groupMember = GroupMember.query.filter_by(group_id=group_id, user_id=current_user.id).first_or_404()
    group_name = Group.query.filter_by(id=group_id).first_or_404().name
    db.session.delete(groupMember)
    db.session.commit()
    return redirect(url_for('main.group', groupname=group_name))

@bp.route('/delete_group/<group_id>', methods=['POST'])
@login_required
def delete_group(group_id):
    group = Group.query.filter_by(id=group_id).first_or_404()
    db.session.delete(group)
    db.session.commit()
    return redirect(url_for('main.index'))


@bp.route('/delete_account/<user_id>', methods=['POST'])
@login_required
def delete_account(user_id):
    user = User.query.filter_by(id=user_id).first_or_404()
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('auth.logout'))

@bp.route('/explore', methods=['GET'])
@login_required
def explore():
    page_group = request.args.get('page_group', 1, type=int)
    page_user = request.args.get('page_user', 1, type=int)
    groups = Group.query.paginate(page=page_group, per_page=2)
    users = User.query.paginate(page=page_user, per_page=2)
    return render_template('explore.html', title='index', groups=groups, users=users)


@bp.route('/create_expense/<group_id>', methods=['GET', 'POST'])
@login_required
def create_expense(group_id):
    group = Group.query.filter_by(id=group_id).first_or_404()
    form = CreateExpense(group_id, current_user.id)
    if form.validate_on_submit():
        lender = GroupMember.query.filter_by(group_id=group_id, user_id=current_user.id).first_or_404()
        expense = Expense(title=form.title.data, amount=form.amount.data, description=form.description.data, lender_id=lender.id, group_id=group_id, is_paid=False)
        db.session.add(expense)
        expense.add_members(form.members.data)
        db.session.commit()
        expense.set_amount_borrowed()
        db.session.commit()
        flash(f'Expense - {expense.title} has been created.', 'success')
        return redirect(url_for('main.index'))
    return render_template('create_expense.html', title='Create expense', form=form, groupname=group.name)


@bp.route('/remove_expense/<expense_id>', methods=['POST'])
@login_required
def remove_expense(expense_id):
    Expense.query.filter_by(id=expense_id).delete()
    db.session.commit()
    return redirect(url_for('main.index'))

@bp.route('/create_transaction/<expense_id>', methods=['GET', 'POST'])
@login_required
def create_transaction(expense_id):
    expense = Expense.query.filter_by(id=expense_id).first_or_404()
    form = CreateTransaction(expense_id, user=current_user)
    user_as_expense_member = (
            db.session.query(ExpenseMember)
            .join(GroupMember)
            .filter(GroupMember.user_id == current_user.id, ExpenseMember.expense_id == expense_id)
            .first()
        )
    if form.validate_on_submit():
        print(form.date.data)
        transaction = Transaction(expense_id=expense_id, expense_member_id=user_as_expense_member.id, amount=form.amount.data, note=form.note.data, date=form.date.data)
        db.session.add(transaction)
        db.session.commit()
        flash(f'Transaction for {expense.title} has been registered.', 'success')
        return redirect(url_for('main.index'))
    return render_template('create_transaction.html', title='Create transaction', form=form, expense=expense)