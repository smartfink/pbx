%define modname pbx

Summary: Issabel PBX Module
Name:    issabel-%{modname}
Version: 4.0.0
Release: 1
License: GPL
Group:   Applications/System
Source0: %{modname}_%{version}-%{release}.tgz
BuildRoot: %{_tmppath}/%{name}-%{version}-root
BuildArch: noarch
Requires(pre): issabel-framework >= 4.0.0-1
Requires(pre): issabel-my_extension >= 2.0.4-5
Requires(pre): issabel-system >= 2.3.0-10
Requires(pre): vsftpd
Requires(pre): asterisk >= 1.8
Requires: festival >= 1.95
Requires(pre): issabelPBX >= 2.11.0-1

Requires: issabel-endpointconfig2 >= 4.0.0-1

# commands: mv chown
Requires: coreutils

# commands: sed
Requires: sed

# commands: grep
Requires: grep

# commands: /usr/bin/killall
Requires: psmisc

# commands: /usr/bin/sqlite3
Requires: sqlite

# commands: /sbin/chkconfig
Requires: chkconfig

Requires: /sbin/pidof

Obsoletes: elastix-pbx

%description
Issabel PBX Module

%prep
%setup -n %{name}_%{version}-%{release}

%install
rm -rf $RPM_BUILD_ROOT

# Asterisk files
mkdir -p $RPM_BUILD_ROOT/var/lib/asterisk/agi-bin
mkdir -p $RPM_BUILD_ROOT/var/lib/asterisk/mohmp3

mkdir -p $RPM_BUILD_ROOT/etc/cron.daily

# ** /bin path ** #
mkdir -p $RPM_BUILD_ROOT/bin

# Files provided by all Elastix modules
mkdir -p    $RPM_BUILD_ROOT/var/www/html/
mv modules/ $RPM_BUILD_ROOT/var/www/html/

# ** files ftp ** #
#mkdir -p $RPM_BUILD_ROOT/var/ftp/config

# ** /asterisk path ** #
mkdir -p $RPM_BUILD_ROOT/etc/asterisk/

# ** service festival ** #
mkdir -p $RPM_BUILD_ROOT/etc/init.d/
mkdir -p $RPM_BUILD_ROOT/var/log/festival/

# The following folder should contain all the data that is required by the installer,
# that cannot be handled by RPM.
mkdir -p      $RPM_BUILD_ROOT/usr/share/elastix/module_installer/%{name}-%{version}-%{release}/
mkdir -p      $RPM_BUILD_ROOT/usr/share/elastix/privileged/

# crons config
mv setup/etc/cron.daily/asterisk_cleanup      $RPM_BUILD_ROOT/etc/cron.daily/
chmod 755 $RPM_BUILD_ROOT/etc/cron.daily/*
rmdir setup/etc/cron.daily/

# ** asterisk.reload file ** #
mv setup/bin/asterisk.reload                  $RPM_BUILD_ROOT/bin/
chmod 755 $RPM_BUILD_ROOT/bin/asterisk.reload
rmdir setup/bin

# ** files asterisk for agi-bin and mohmp3 ** #
mv setup/asterisk/agi-bin/*                   $RPM_BUILD_ROOT/var/lib/asterisk/agi-bin/
chmod 755 $RPM_BUILD_ROOT/var/lib/asterisk/agi-bin/*
mv setup/asterisk/mohmp3/*                    $RPM_BUILD_ROOT/var/lib/asterisk/mohmp3/
rmdir setup/asterisk/*
rmdir setup/asterisk

# Moviendo archivos festival y sip_notify_custom_elastix.conf
chmod +x setup/etc/asterisk/sip_notify_custom_elastix.conf
chmod +x setup/etc/init.d/festival
mv setup/etc/asterisk/sip_notify_custom_elastix.conf      $RPM_BUILD_ROOT/etc/asterisk/
mv setup/etc/init.d/festival                              $RPM_BUILD_ROOT/etc/init.d/
mv setup/usr/share/elastix/privileged/*                   $RPM_BUILD_ROOT/usr/share/elastix/privileged/
mv setup/etc/httpd/                                       $RPM_BUILD_ROOT/etc/
rmdir setup/etc/init.d
rmdir setup/etc/asterisk
rmdir setup/usr/share/elastix/privileged

rmdir setup/usr/share/elastix setup/usr/share setup/usr

chmod +x setup/migrationFilesMonitor*php
mv setup/     $RPM_BUILD_ROOT/usr/share/elastix/module_installer/%{name}-%{version}-%{release}/
mv menu.xml   $RPM_BUILD_ROOT/usr/share/elastix/module_installer/%{name}-%{version}-%{release}/


%pre
#Para migrar monitor
touch /tmp/migration_version_monitor.info
rpm -q --queryformat='%{VERSION}\n%{RELEASE}' elastix > /tmp/migration_version_monitor.info

# TODO: TAREA DE POST-INSTALACIÓN
#useradd -d /var/ftp -M -s /sbin/nologin ftpuser

# Try to fix mess left behind by previous packages.
if [ -e /etc/vsftpd.user_list ] ; then
    echo "   NOTICE: broken vsftpd detected, will try to fix..."
    cp /etc/vsftpd.user_list /tmp/
fi

mkdir -p /usr/share/elastix/module_installer/%{name}-%{version}-%{release}/
touch /usr/share/elastix/module_installer/%{name}-%{version}-%{release}/preversion_%{modname}.info
if [ $1 -eq 2 ]; then
    rpm -q --queryformat='%{VERSION}-%{RELEASE}' %{name} > /usr/share/elastix/module_installer/%{name}-%{version}-%{release}/preversion_%{modname}.info
fi

%post
######### Para ejecucion del migrationFilesMonitor.php ##############

#/usr/share/elastix/migration_version_monitor.info
#obtener la primera linea que contiene la version

vers=`sed -n '1p' "/tmp/migration_version_monitor.info"`
if [ "$vers" = "1.6.2" ]; then
  rels=`sed -n '2p' "/tmp/migration_version_monitor.info"`
  if [ $rels -le 13 ]; then # si el release es menor o igual a 13 entonces ejecuto el script

    echo "Executing process migration audio files Monitor"
    chmod +x /usr/share/elastix/module_installer/%{name}-%{version}-%{release}/setup/migrationFilesMonitor.php
    php /usr/share/elastix/module_installer/%{name}-%{version}-%{release}/setup/migrationFilesMonitor.php
  fi
fi
rm -rf /tmp/migration_version_monitor.info
###################################################################

varwriter=0

if [ -f "/etc/asterisk/extensions_override_freepbx.conf" ]; then
    echo "File extensions_override_freepbx.conf in asterisk exits, verifying macro record-enable and hangupcall exists..."
    grep "#include extensions_override_issabel.conf" /etc/asterisk/extensions_override_freepbx.conf &>/dev/null
    res=$?
    if [ $res -eq 1 ]; then #macro record-enable not exists
	echo "#include extensions_override_issabel.conf" > /tmp/ext_over_freepbx.conf
        cat /etc/asterisk/extensions_override_freepbx.conf >> /tmp/ext_over_freepbx.conf
        cat /tmp/ext_over_freepbx.conf > /etc/asterisk/extensions_override_freepbx.conf
	rm -rf /tmp/ext_over_freepbx.conf
        echo "macros elastix was written."
    fi
else
    echo "File extensions_override_freepbx.conf in asterisk not exits, copying include macros elastix..."
    touch /etc/asterisk/extensions_override_freepbx.conf
    echo "#include extensions_override_issabel.conf" > /etc/asterisk/extensions_override_freepbx.conf
fi

# se verifica si extensions_override_issabel.conf usa audio: sin migrar
if [ -f "/etc/asterisk/extensions_override_issabel.conf" ]; then
    if grep -q 'audio:' /etc/asterisk/extensions_override_issabel.conf ; then
        echo "/etc/asterisk/extensions_override_issabel.conf contains CDR(userfield)=audio: , migrating database..."
        /usr/share/elastix/module_installer/%{name}-%{version}-%{release}/setup/migrationFilesMonitor2.php
    fi
fi

# verifico si se incluye a sip_notify_custom_elastix.conf
if [ -f "/etc/asterisk/sip_notify_custom.conf" ]; then
    echo "/etc/asterisk/sip_notify_custom.conf exists, verifying the inclusion of sip_notify_custom_elastix.conf"
    grep "#include sip_notify_custom_elastix.conf" /etc/asterisk/sip_notify_custom.conf &> /dev/null
    if [ $? -eq 1 ]; then
	echo "including sip_notify_custom_elastix.conf..."
	echo "#include sip_notify_custom_elastix.conf" > /tmp/custom_elastix.conf
	cat /etc/asterisk/sip_notify_custom.conf >> /tmp/custom_elastix.conf
	cat /tmp/custom_elastix.conf > /etc/asterisk/sip_notify_custom.conf
	rm -rf /tmp/custom_elastix.conf
    else
	echo "sip_notify_custom_elastix.conf is already included"
    fi
else
    echo "creating file /etc/asterisk/sip_notify_custom.conf"
    touch /etc/asterisk/sip_notify_custom.conf
    echo "#include sip_notify_custom_elastix.conf" > /etc/asterisk/sip_notify_custom.conf
fi

varwriter=1
mv /usr/share/elastix/module_installer/%{name}-%{version}-%{release}/setup/extensions_override_issabel.conf /etc/asterisk/
chown -R asterisk.asterisk /etc/asterisk

if [ $varwriter -eq 1  ]; then
    service asterisk status &>/dev/null
    res2=$?
    if [ $res2 -eq 0  ]; then #service is up
         service asterisk reload
    fi
fi

pathModule="/usr/share/elastix/module_installer/%{name}-%{version}-%{release}"
# Run installer script to fix up ACLs and add module to Elastix menus.
elastix-menumerge /usr/share/elastix/module_installer/%{name}-%{version}-%{release}/menu.xml

pathSQLiteDB="/var/www/db"
mkdir -p $pathSQLiteDB
preversion=`cat $pathModule/preversion_%{modname}.info`
rm -f $pathModule/preversion_%{modname}.info

if [ $1 -eq 1 ]; then #install
  # The installer database
  elastix-dbprocess "install" "/usr/share/elastix/module_installer/%{name}-%{version}-%{release}/setup/db"
elif [ $1 -eq 2 ]; then #update
  # The installer database
   elastix-dbprocess "update"  "$pathModule/setup/db" "$preversion"
fi

#verificando si existe el menu en pbx
path="/var/www/db/acl.db"
path2="/var/www/db/menu.db"
id_menu="control_panel"

#obtenemos el id del recurso (EOP)
res=`sqlite3 $path "select id from acl_resource  where name='control_panel'"`

#obtenemos el id del grupo operador
opid=`sqlite3 $path "select id from acl_group  where name='Operator'"`

if [ $res ]; then #debe de existir el recurso EOP
   if [ $opid ]; then #debe de existir el grupo operador
      val=`sqlite3 $path "select * from acl_group_permission where id_group=$opid and id_resource=$res"`
      if [ -z $val ]; then #se pregunta si existe el permiso de EOP para el grupo Operador
         echo "updating group Operator with permissions in Control Panel Module"
	 `sqlite3 $path "insert into acl_group_permission(id_action, id_group, id_resource) values(1,$opid,$res)"`
      fi
   fi
fi

# The installer script expects to be in /tmp/new_module
mkdir -p /tmp/new_module/%{modname}
cp -r /usr/share/elastix/module_installer/%{name}-%{version}-%{release}/* /tmp/new_module/%{modname}/
chown -R asterisk.asterisk /tmp/new_module/%{modname}

php /tmp/new_module/%{modname}/setup/installer.php
rm -rf /tmp/new_module

# Detect need to fix up vsftpd configuration
if [ -e /tmp/vsftpd.user_list ] ; then
    echo "   NOTICE: fixing up vsftpd configuration..."
    # userlist_deny=NO
    sed --in-place "s,userlist_deny=NO,#userlist_deny=NO,g" /etc/vsftpd/vsftpd.conf
    rm -f /tmp/vsftpd.user_list
fi

# Remove old endpoints_batch menu item
elastix-menuremove endpoints_batch

%clean
rm -rf $RPM_BUILD_ROOT

%preun
if [ $1 -eq 0 ] ; then # Validation for desinstall this rpm; delete
pathModule="/usr/share/elastix/module_installer/%{name}-%{version}-%{release}"
  echo "Delete System menus"
  elastix-menuremove "pbxconfig"

  echo "Dump and delete %{name} databases"
  elastix-dbprocess "delete" "$pathModule/setup/db"
fi

%files
%defattr(-, asterisk, asterisk)
/etc/asterisk/sip_notify_custom_elastix.conf
/var/lib/asterisk/*
/var/lib/asterisk/agi-bin
/var/log/festival
/usr/share/elastix/module_installer/%{name}-%{version}-%{release}/setup/extensions_override_issabel.conf
%defattr(-, root, root)
%{_localstatedir}/www/html/*
/usr/share/elastix/module_installer/*
%defattr(644, root, root)
%config(noreplace) /etc/httpd/conf.d/*
%defattr(755, root, root)
/etc/init.d/festival
/bin/asterisk.reload
/usr/share/elastix/privileged/*
/var/lib/asterisk/agi-bin/*
/etc/cron.daily/asterisk_cleanup

%changelog
