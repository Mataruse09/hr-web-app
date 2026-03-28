from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, session,
)
from utils import login_required, roles_required
from models import employee_model

employee_bp = Blueprint('employees', __name__)


@employee_bp.route('/')
@login_required
def list_employees():
    company_id = session['company_id']
    search     = request.args.get('q', '').strip()
    employees  = (
        employee_model.search(company_id, search)
        if search else
        employee_model.get_all(company_id)
    )
    return render_template('employees/list.html',
                           employees=employees, search=search)


@employee_bp.route('/add', methods=['GET', 'POST'])
@login_required
@roles_required('Admin', 'HR')
def add_employee():
    company_id  = session['company_id']
    departments = employee_model.get_departments(company_id)
    next_code   = employee_model.get_next_employee_code(company_id)

    if request.method == 'POST':
        data = request.form.to_dict()
        try:
            emp_id = employee_model.create(company_id, data)
            flash('Employee added successfully.', 'success')
            return redirect(url_for('employees.profile', emp_id=emp_id))
        except Exception as e:
            flash(f'Error adding employee: {str(e)}', 'danger')

    return render_template('employees/form.html',
                           action='add', departments=departments,
                           next_code=next_code, employee=None)


@employee_bp.route('/<int:emp_id>/edit', methods=['GET', 'POST'])
@login_required
@roles_required('Admin', 'HR')
def edit_employee(emp_id):
    company_id  = session['company_id']
    employee    = employee_model.get_by_id(emp_id, company_id)
    departments = employee_model.get_departments(company_id)

    if not employee:
        flash('Employee not found.', 'warning')
        return redirect(url_for('employees.list_employees'))

    if request.method == 'POST':
        data = request.form.to_dict()
        try:
            employee_model.update(emp_id, company_id, data)
            flash('Employee updated successfully.', 'success')
            return redirect(url_for('employees.profile', emp_id=emp_id))
        except Exception as e:
            flash(f'Error updating employee: {str(e)}', 'danger')

    return render_template('employees/form.html',
                           action='edit', departments=departments,
                           employee=employee, next_code=None)


@employee_bp.route('/<int:emp_id>')
@login_required
def profile(emp_id):
    company_id = session['company_id']
    employee   = employee_model.get_by_id(emp_id, company_id)
    if not employee:
        flash('Employee not found.', 'warning')
        return redirect(url_for('employees.list_employees'))
    from models import payroll_model, leave_model, attendance_model
    from datetime import date
    comp    = payroll_model.get_compensation(emp_id, company_id)
    balance = leave_model.get_balance(emp_id, company_id, date.today().year)
    return render_template('employees/profile.html',
                           employee=employee, comp=comp, balance=balance)


@employee_bp.route('/<int:emp_id>/delete', methods=['POST'])
@login_required
@roles_required('Admin')
def delete_employee(emp_id):
    company_id = session['company_id']
    employee_model.delete(emp_id, company_id)
    flash('Employee deleted.', 'info')
    return redirect(url_for('employees.list_employees'))