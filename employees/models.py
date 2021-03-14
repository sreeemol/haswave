from django.db import models
from django.utils import timezone

from django.utils.translation import gettext_lazy as _

from general.models import Base, Country, State, City, PermissionGroup
from accounts.models import User
from organizations.models import Organization,Branch
from departments.models import Designation


class Employee(Base):
    """
    Employee model associated with details of an employee
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='employee_user')
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT)
    branch = models.ForeignKey(Branch, null=True, blank=True, on_delete=models.PROTECT)
    department = models.ForeignKey('departments.Department', null=True, blank=True, on_delete=models.PROTECT)
    designation = models.ForeignKey(Designation, on_delete=models.PROTECT)
    photo = models.ImageField(upload_to='employee/', null=True, blank=True)
    first_name = models.CharField(max_length=128)
    last_name = models.CharField(max_length=128)
    phone = models.CharField(max_length=16, null=True, blank=True)
    nationality = models.ForeignKey(Country, on_delete=models.PROTECT)
    state = models.ForeignKey(State, null=True, blank=True, on_delete=models.PROTECT)
    city = models.ForeignKey(City, null=True, blank=True, on_delete=models.PROTECT)
    house_name = models.CharField(_('House name / flat No'), null=True, blank=True, max_length=128)
    street_name = models.CharField(_('Street Name / No'), null=True, blank=True, max_length=128)
    locality_name = models.CharField(_('Locality Name / No'), null=True, blank=True, max_length=128)
    pin_code = models.CharField(_('Zip Code'), null=True, blank=True, max_length=20)
    permission_groups = models.ManyToManyField(PermissionGroup)
    invitation_accepted = models.BooleanField(default=False)

    def __str__(self):
        return self.first_name +" "+ self.last_name

    class Meta(Base.Meta):
        default_permissions = ()

        permissions = (
            ("add_employee", "Can add employee"),
            ("change_employee", "Can change employee"),
            ("view_employee", "Can view employee"),
            ("update_status", "Can update status"),
            ("view_permissions", "Can view permissions"),
            ("change_permissions", "Can change permissions"),
            ("view_tracker_info", "Can view tracker info"),
            ("change_tracker_info", "Can change tracker info"),
        )

    @property
    def employee_status(self):

        if not self.invitation_accepted:
            return 'Invited'

        if self.user.is_active:
            return 'Active'

        return 'Inactive'


class EmployeeTrackerInfo(models.Model):
    """
    Model to hold details about tracker identification
    """
    employee = models.OneToOneField(Employee, on_delete=models.PROTECT, related_name='employee_tracker_info')
    card_id = models.CharField(max_length=128, blank=True)
    employee_ID = models.CharField(max_length=128, null=True, unique=True)


def screenshot_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/employee_screenshot/<year>/<month>/<day>/<employee slug>/<filename>
    
    return 'employee_screenshot/{year}/{month}/{day}/{slug}/{filename}'.format(
        year = timezone.now().year,
        month = timezone.now().month,
        day = timezone.now().day,
        slug = instance.employee.slug, 
        filename = filename
    )


class EmployeeScreenshot(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='employee_screen_short')
    datetime = models.DateTimeField()
    screenshot = models.ImageField(upload_to=screenshot_path)