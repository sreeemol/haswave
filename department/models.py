from django.db import models
from django.contrib.auth.models import Permission


from general.models import Base, PermissionGroup
from accounts.models import User
from organizations.models import Organization, Branch


def department_image_path(instance, filename):
    return 'departments/{0}/{1}'.format(instance.organization.organization_name, filename)


class Department(Base):
    """
    department model associated with details of the department
    """
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT)
    branch = models.ForeignKey(Branch, null=True, blank=True, on_delete=models.PROTECT)
    department_name = models.CharField(max_length=128)
    description = models.TextField(null=True, blank=True)
    image = models.ImageField(null=True, blank=True, upload_to=department_image_path)

    class Meta:
        unique_together = ("department_name", "organization", "branch")
        
    def __str__(self):
        return self.department_name


class Designation(Base):
    """
    designation model associated with designation details of the respective department
    """
    organization = models.ForeignKey(Organization, null=True, blank=True, on_delete=models.PROTECT)
    designation_name = models.CharField(max_length=128)
    permission_groups = models.ManyToManyField(PermissionGroup, blank=True)
    weight = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("organization", "designation_name")

    def __str__(self):
        return self.designation_name


class Team(Base):
    """
    team model associated with team,parent team details of the respective departments
    """
    department = models.ForeignKey(Department, on_delete=models.PROTECT)
    team_name = models.CharField(max_length=128)
    parent_team = models.ForeignKey("self", null=True, blank=True, limit_choices_to={'parent_team': None},
                                    related_name='sub_teams', on_delete=models.PROTECT)

    def __str__(self):
        return self.team_name
