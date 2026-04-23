# PERMISSIONS MATRIX - HR Management System

Last Updated: 2026-04-22

## Overview
This document defines the complete permission structure for the HR Management System. Each role has specific access levels to features and data.

---

## ROLE HIERARCHY

| Role | Level | Scope |
|------|-------|-------|
| **Admin** | 999 | Full system access, all features |
| **CHRO** | 800 | Strategic HR operations (except System Settings) |
| **HR** | 700 | Operational HR management (except permanent employee deletion) |
| **Manager** | 600 | Team-level management (RESTRICTED from Payroll) |
| **Employee** | 100 | Self-service only (view own data, uneditable) |

---

## DETAILED PERMISSION MATRIX

### ADMIN (999)
**Access Level**: Complete system access

| Feature | View | Create | Edit | Delete | Approve | Notes |
|---------|------|--------|------|--------|---------|-------|
| **Employees** | ✅ All | ✅ | ✅ | ✅ (Permanent) | N/A | Full CRUD access |
| **Attendance** | ✅ All | ✅ | ✅ | ✅ | N/A | Mark & view all |
| **Leave** | ✅ All | ✅ | ✅ | ✅ | ✅ | Manage leave requests |
| **Payroll** | ✅ All | ✅ | ✅ Edit | ❌ | ✅ | Process & approve payroll |
| **Appraisals** | ✅ All | ✅ | ✅ | ✅ | ✅ | Create, review, manage all |
| **Compliance** | ✅ All | ✅ | ✅ | ✅ | ✅ | Assign & manage policies |
| **Gamification** | ✅ All | ✅ | ✅ | ✅ | ✅ | Award points, manage badges |
| **Forecasting** | ✅ All | ✅ | ✅ | ✅ | N/A | Create & manage forecasts |
| **Attrition** | ✅ All | ✅ | ✅ | ✅ | ✅ | Record exits, view analytics |
| **Activity Logs** | ✅ | ❌ | ❌ | ❌ | N/A | View all audit logs |
| **User Management** | ✅ | ✅ Create | ✅ | ✅ | N/A | Create/manage users |
| **System Settings** | ✅ | ✅ | ✅ | ❌ | N/A | Configure system |

**Restrictions**: None

---

### CHRO (800)
**Access Level**: Strategic HR - All features EXCEPT System Settings, User Management, Payroll Approval

| Feature | View | Create | Edit | Delete | Approve | Notes |
|---------|------|--------|------|--------|---------|-------|
| **Employees** | ✅ All | ❌ | ❌ | ❌ | N/A | View-only on employee data |
| **Attendance** | ✅ All | ❌ | ❌ | ❌ | N/A | View-only, cannot mark |
| **Leave** | ✅ All | ❌ | ❌ | ❌ | ❌ | View all leave, cannot approve |
| **Payroll** | ✅ View | ❌ | ❌ | ❌ | ❌ | View payroll runs only (NO edit/approve) |
| **Appraisals** | ✅ All | ✅ | ✅ | ❌ | ✅ | Create & review appraisals |
| **Compliance** | ✅ All | ✅ | ✅ | ❌ | ✅ | Assign & manage compliance |
| **Gamification** | ✅ All | ✅ | ❌ | ❌ | ✅ | Award points, view leaderboard |
| **Forecasting** | ✅ All | ✅ | ✅ | ❌ | N/A | Create & view forecasts |
| **Attrition** | ✅ All | ❌ | ❌ | ❌ | N/A | View analytics only |
| **Activity Logs** | ✅ | ❌ | ❌ | ❌ | N/A | View audit logs |
| **User Management** | ❌ | ❌ | ❌ | ❌ | N/A | **RESTRICTED** |
| **System Settings** | ❌ | ❌ | ❌ | ❌ | N/A | **RESTRICTED** |

**Restrictions**:
- ❌ Cannot access System Settings
- ❌ Cannot manage users
- ❌ Cannot process/approve payroll (view-only)
- ❌ Cannot delete any records
- ❌ Cannot create/edit employees

---

### HR (700)
**Access Level**: Operational HR - Full features EXCEPT permanent employee deletion and system settings

| Feature | View | Create | Edit | Delete | Approve | Notes |
|---------|------|--------|------|--------|---------|-------|
| **Employees** | ✅ All | ✅ | ✅ | ❌ (Soft Delete Only) | N/A | Cannot permanently delete |
| **Attendance** | ✅ All | ✅ | ✅ | ✅ | N/A | Mark & manage attendance |
| **Leave** | ✅ All | ✅ | ✅ | ✅ | ✅ | Approve leave requests |
| **Payroll** | ✅ All | ✅ | ✅ Edit | ❌ | ✅ | Process & approve payroll |
| **Appraisals** | ✅ All | ✅ | ✅ | ✅ | ✅ | Create, review, manage all |
| **Compliance** | ✅ All | ✅ | ✅ | ✅ | ✅ | Assign & manage policies |
| **Gamification** | ✅ All | ✅ | ✅ | ❌ | ✅ | Award points, manage leaderboard |
| **Forecasting** | ✅ All | ✅ | ✅ | ❌ | N/A | Create & manage forecasts |
| **Attrition** | ✅ All | ✅ | ✅ | ❌ | N/A | Record exits, view analytics |
| **Activity Logs** | ✅ | ❌ | ❌ | ❌ | N/A | View audit logs |
| **User Management** | ❌ | ❌ | ❌ | ❌ | N/A | **RESTRICTED** |
| **System Settings** | ❌ | ❌ | ❌ | ❌ | N/A | **RESTRICTED** |

**Restrictions**:
- ❌ Cannot permanently delete employees (soft delete only)
- ❌ Cannot access System Settings
- ❌ Cannot manage users
- ❌ Cannot delete compliance/forecasting/attrition records

---

### MANAGER (600)
**Access Level**: Team-level - RESTRICTED from Payroll, Forecasting, Attrition Analytics

| Feature | View | Create | Edit | Delete | Approve | Notes |
|---------|------|--------|------|--------|---------|-------|
| **Employees** | ✅ Team Only | ✅ Team | ✅ Team | ❌ | N/A | Department-scoped only |
| **Attendance** | ✅ Team Only | ✅ | ✅ Team | ❌ | N/A | Mark team attendance |
| **Leave** | ✅ Team Only | ❌ | ❌ | ❌ | ✅ | Approve team leave |
| **Payroll** | ❌ | ❌ | ❌ | ❌ | ❌ | **DENIED - Cannot access** |
| **Appraisals** | ✅ Team Only | ✅ | ✅ Team | ❌ | ✅ | Review team appraisals |
| **Compliance** | ✅ Team Only | ✅ | ✅ Team | ❌ | ❌ | Assign to team |
| **Gamification** | ✅ All (Leaderboard) | ❌ | ❌ | ❌ | ✅ | Award points to team |
| **Forecasting** | ❌ | ❌ | ❌ | ❌ | N/A | **RESTRICTED** |
| **Attrition** | ❌ | ❌ | ❌ | ❌ | N/A | **RESTRICTED** |
| **Activity Logs** | ❌ | ❌ | ❌ | ❌ | N/A | **RESTRICTED** |
| **User Management** | ❌ | ❌ | ❌ | ❌ | N/A | **RESTRICTED** |
| **System Settings** | ❌ | ❌ | ❌ | ❌ | N/A | **RESTRICTED** |

**Restrictions**:
- ❌ **PAYROLL COMPLETELY HIDDEN** - Cannot view, edit, or access any payroll data
- ❌ Cannot see Forecasting
- ❌ Cannot see Attrition analytics
- ❌ Can only manage their own department
- ❌ Cannot delete employees
- ❌ Cannot manage system or users

---

### EMPLOYEE (100)
**Access Level**: Self-service only - VIEW OWN DATA ONLY (uneditable)

| Feature | View | Create | Edit | Delete | Approve | Notes |
|---------|------|--------|------|--------|---------|-------|
| **Own Profile** | ✅ Own | ❌ | ❌ | ❌ | N/A | View-only, uneditable |
| **Own Attendance** | ✅ Own | ❌ | ❌ | ❌ | N/A | View-only attendance records |
| **Own Leave** | ✅ Own | ✅ Request | ❌ | ❌ | ❌ | Can request leave only |
| **Own Payroll** | ✅ Own | ❌ | ❌ | ❌ | N/A | View-only payroll slips |
| **Own Appraisals** | ✅ Own | ❌ | ❌ | ❌ | ❌ | View reviews, cannot edit |
| **Own Compliance** | ✅ Own | ❌ | ❌ | ❌ | ✅ Mark Complete | View tasks, mark completed |
| **Gamification** | ✅ Leaderboard + Own Profile | ❌ | ❌ | ❌ | N/A | View leaderboard & own profile |
| **Forecasting** | ❌ | ❌ | ❌ | ❌ | N/A | **HIDDEN** |
| **Attrition** | ❌ | ❌ | ❌ | ❌ | N/A | **HIDDEN** |
| **Activity Logs** | ❌ | ❌ | ❌ | ❌ | N/A | **HIDDEN** |
| **User Management** | ❌ | ❌ | ❌ | ❌ | N/A | **HIDDEN** |
| **System Settings** | ❌ | ❌ | ❌ | ❌ | N/A | **HIDDEN** |

**Restrictions**:
- ❌ Can ONLY view their own data
- ❌ All data is READ-ONLY (uneditable)
- ❌ Cannot see any other employee's information
- ❌ Cannot access any admin functions
- ❌ Can only REQUEST leave (not approve)
- ❌ Can mark compliance tasks as complete

---

## SYSTEM-WIDE RESTRICTIONS

### Feature Restrictions by Role
```
┌─────────────────────────────────────────────────────┐
│ PERMANENT EMPLOYEE DELETION                         │
├─────────────────────────────────────────────────────┤
│ ✅ Admin only                                       │
│ ❌ HR cannot permanently delete (soft delete only)  │
│ ❌ CHRO cannot delete                               │
│ ❌ Manager cannot delete                            │
│ ❌ Employee cannot delete                           │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ PAYROLL MANAGEMENT                                  │
├─────────────────────────────────────────────────────┤
│ ✅ Admin - Full access (process, approve, edit)    │
│ ✅ HR - Full access (process, approve, edit)       │
│ ⚠️ CHRO - View-only (cannot process/approve)       │
│ ❌ Manager - COMPLETE DENIAL (hidden from menu)    │
│ ❌ Employee - Cannot access                        │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ SYSTEM SETTINGS & CONFIGURATION                     │
├─────────────────────────────────────────────────────┤
│ ✅ Admin only                                       │
│ ❌ CHRO explicitly denied (despite HR privileges)   │
│ ❌ HR cannot access                                 │
│ ❌ Manager cannot access                           │
│ ❌ Employee cannot access                          │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ USER MANAGEMENT & PERMISSIONS                       │
├─────────────────────────────────────────────────────┤
│ ✅ Admin only                                       │
│ ❌ CHRO cannot manage users                        │
│ ❌ HR cannot manage users                          │
│ ❌ Manager cannot manage users                     │
│ ❌ Employee cannot manage users                    │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ FORECASTING & LABOUR PLANNING                       │
├─────────────────────────────────────────────────────┤
│ ✅ Admin - Full access (create, edit, view)        │
│ ✅ HR - Full access (create, edit, view)           │
│ ✅ CHRO - Full access (create, edit, view)         │
│ ❌ Manager - HIDDEN (cannot access)                │
│ ❌ Employee - HIDDEN (cannot access)               │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ ATTRITION ANALYTICS                                 │
├─────────────────────────────────────────────────────┤
│ ✅ Admin - Full access (record exits, view trends) │
│ ✅ HR - Full access (record exits, view trends)    │
│ ✅ CHRO - View-only (cannot record exits)          │
│ ❌ Manager - HIDDEN (cannot access)                │
│ ❌ Employee - HIDDEN (cannot access)               │
└─────────────────────────────────────────────────────┘
```

---

## DATA SCOPE RESTRICTIONS

### Employee Data Visibility
```
Admin:     Can see ALL employees, all departments
HR:        Can see ALL employees, all departments
CHRO:      Can see ALL employees, all departments (view-only)
Manager:   Can see only their department's employees
Employee:  Can see only their own profile
```

### Attendance & Leave Scope
```
Admin:     Can view/manage ALL attendance & leave
HR:        Can view/manage ALL attendance & leave
Manager:   Can view/manage only their team's attendance & leave
Employee:  Can view only their own attendance & leave
           Can REQUEST leave, cannot approve
```

### Payroll Data Visibility
```
Admin:     Can view/edit/process ALL payroll
HR:        Can view/edit/process ALL payroll
CHRO:      Can view payroll runs (no editing)
Manager:   **DENIED** - Cannot see any payroll data
Employee:  Can view only their own payroll slip (view-only)
```

---

## ROUTE-LEVEL ENFORCEMENT

### Protected Endpoints by Decorator

**`@allow_chro_except_settings`** - Used on sensitive endpoints
- Allows: Admin only
- Denies: CHRO, HR, Manager, Employee
- Routes: `/admin/settings*`

**`@allow_hr_except_delete`** - Used on deletion endpoints
- Allows: Admin only
- Denies: HR (no permanent delete), CHRO, Manager, Employee
- Routes: `/employees/delete/<id>`

**`@deny_manager_from_payroll`** - Used on all payroll routes
- Allows: Admin, HR, CHRO
- Denies: Manager, Employee
- Routes: `/payroll/*`

**`@allow_employee_own_data_only`** - Used on employee-accessible routes
- Employee scope: Can only access own data
- Manager scope: Can only access own department
- Routes: `/attendance/logs`, `/leave/view`, `/payroll/slip`

**`@require_data_ownership`** - Used for sensitive data access
- Validates data ownership at record level
- Enforces multi-tenant isolation
- Routes: API endpoints returning sensitive data

---

## TESTING CHECKLIST

### Role Access Tests
- [ ] Admin - Can access ALL features
- [ ] CHRO - Can access HR features but NOT System Settings or Payroll Editing
- [ ] HR - Can access HR features but NOT permanent delete or System Settings
- [ ] Manager - Can access HR features but NOT Payroll (403 on /payroll/*)
- [ ] Employee - Can only view own data (403 on others' data)

### Data Scope Tests
- [ ] Employee cannot view other employees' attendance
- [ ] Employee cannot view any payroll data
- [ ] Manager cannot access /payroll routes (denied or redirected)
- [ ] Manager can only see their department employees
- [ ] CHRO cannot modify employee data (403 on edit endpoints)

### Feature Visibility Tests
- [ ] Payroll NOT in Manager dashboard/menu
- [ ] Forecasting NOT in Manager/Employee menu
- [ ] Attrition Analytics NOT in Manager/Employee menu
- [ ] Compliance visible to Manager but team-scoped
- [ ] System Settings link only visible to Admin

### Permission Enforcement Tests
- [ ] Hard delete returns 403 for HR role
- [ ] Settings endpoints return 403 for CHRO role
- [ ] Payroll endpoints return 403/redirect for Manager
- [ ] Employee data returns 403 when accessed by different Employee
- [ ] Breadcrumb shows current user's accessible scope

---

## IMPLEMENTATION NOTES

### Database Permissions Table
Seed data enforces these roles in `permissions` table:
```sql
INSERT INTO permissions (role, permission) VALUES
-- Admin
('Admin', 'view_all_employees'), ('Admin', 'edit_all_employees'), 
('Admin', 'delete_employee_permanent'), ('Admin', 'view_payroll'), 
('Admin', 'edit_payroll'), ('Admin', 'approve_payroll'),
('Admin', 'manage_system_settings'), ('Admin', 'manage_users'),

-- HR
('HR', 'view_all_employees'), ('HR', 'edit_all_employees'),
('HR', 'view_payroll'), ('HR', 'edit_payroll'), ('HR', 'approve_payroll'),

-- CHRO
('CHRO', 'view_all_employees'), ('CHRO', 'view_payroll'),
('CHRO', 'manage_appraisals'),

-- Manager
('Manager', 'view_team_employees'), ('Manager', 'view_team_attendance'),
('Manager', 'mark_team_attendance'),

-- Employee
('Employee', 'view_own_profile'), ('Employee', 'view_own_attendance'),
('Employee', 'request_leave');
```

### Session-based Enforcement
All role checks use `session['role']` normalized to lowercase:
```python
role = session.get('role', 'Employee').strip().lower()
```

### Decorator Stacking Order
Use decorators in this order (important):
```python
@route('/path')
@login_required              # First: Check if logged in
@roles_required(...)         # Second: Check role
@allow_manager_no_payroll    # Third: Apply role-specific restrictions
def handler():
    pass
```

---

## FUTURE ENHANCEMENTS

- [ ] Implement granular permission inheritance (sub-roles)
- [ ] Add time-based access (schedule-based permissions)
- [ ] Implement permission delegation (HR can delegate to Manager)
- [ ] Add audit logging for permission changes
- [ ] Create permission conflict detection
- [ ] Build role-based API response filtering (show/hide fields per role)
