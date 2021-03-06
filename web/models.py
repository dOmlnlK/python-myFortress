from django.db import models
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser,PermissionsMixin
)
# Create your models here.

class Host(models.Model):
    """存储主机列表"""
    name = models.CharField(max_length=32,unique=True)
    ip = models.GenericIPAddressField(unique=True)
    port = models.SmallIntegerField(default=22)
    idc = models.ForeignKey("IDC")

    def __str__(self):
        return self.name



class HostCroup(models.Model):
    """存储主机组"""
    name = models.CharField(max_length=32,unique=True)
    host2remote_users = models.ManyToManyField("Host2RemoteUser")

    def __str__(self):
        return self.name

class RemoteUser(models.Model):
    """存储远程要管理的主机的账号"""
    auth_type_choices = ((0,"ssh-password"),(1,"ssh-key"))
    auth_type = models.SmallIntegerField(choices=auth_type_choices,default=0)

    username = models.CharField(max_length=32)
    password = models.CharField(max_length=64,blank=True,null=True)

    class Meta:
        unique_together = ("auth_type","username","password")

    def __str__(self):
        return "%s:%s"%(self.username,self.password)


class Host2RemoteUser(models.Model):
    """绑定主机与远程账号关系"""
    host = models.ForeignKey("Host")
    remote_user = models.ForeignKey("RemoteUser")

    class Meta:
        unique_together = ("host","remote_user")

    def __str__(self):
        return "%s-%s"%(self.host,self.remote_user)


class UserInfoManager(BaseUserManager):
    def create_user(self, email, name, password=None):
        """
        Creates and saves a User with the given email, date of
        birth and password.
        """
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            email=self.normalize_email(email),
            name=name,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password):
        """
        Creates and saves a superuser with the given email, date of
        birth and password.
        """
        user = self.create_user(
            email,
            password=password,
            name=name,
        )
        user.is_superuser = True
        user.save(using=self._db)
        return user



class UserInfo(AbstractBaseUser,PermissionsMixin):
    """堡垒机账号"""
    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,

    )
    name = models.CharField(max_length=64, verbose_name="姓名")

    host2remote_users = models.ManyToManyField("Host2RemoteUser",blank=True,null=True)
    host_groups = models.ManyToManyField("HostCroup",null=True,blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=True)
    #is_admin = models.BooleanField(default=False)


    objects = UserInfoManager()   #变量名必须是objects


    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    def get_full_name(self):
        # The user is identified by their email address
        return self.email

    def get_short_name(self):
        # The user is identified by their email address
        return self.email

    def __str__(self):              # __unicode__ on Python 2
        return self.email


class IDC(models.Model):
    """机房信息"""
    name = models.CharField(max_length=32,unique=True)

    def __str__(self):
        return self.name


class AuditLog(models.Model):
    """审计日志"""
    host2remote_user = models.ForeignKey("Host2RemoteUser")
    user = models.ForeignKey("UserInfo",verbose_name="堡垒机用户")

    log_type_choices = ((0,"login"),(1,"logout"),(2,"cmd"))
    log_type = models.SmallIntegerField(choices=log_type_choices)

    content = models.CharField(max_length=255)
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return "%s-%s"%(self.host2remote_user,self.content)



class Task(models.Model):
    """批量任务"""
    task_type_choices = (('cmd','批量命令'),('file_transfer','文件传输'))
    task_type = models.CharField(choices=task_type_choices,max_length=64)
    content = models.CharField(max_length=255, verbose_name="任务内容")
    user = models.ForeignKey("UserInfo")

    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "%s %s"%(self.task_type,self.content)



class ChildrenTaskResult(models.Model):
    """存储大任务子结果"""
    task = models.ForeignKey("Task")
    host2remote_user = models.ForeignKey("Host2RemoteUser")
    result = models.TextField(verbose_name="任务执行结果")

    status_choices = ((0,'initialized'),(1,'sucess'),(2,'failed'),(3,'timeout'))
    status = models.SmallIntegerField(choices=status_choices,default=0)

    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "%s %s"%(self.task,self.host2remote_user)
