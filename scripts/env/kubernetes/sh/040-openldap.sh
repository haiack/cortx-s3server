#!/bin/bash
#
# Copyright (c) 2021 Seagate Technology LLC and/or its Affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.
#

set -euo pipefail # exit on failures

source ./config.sh
source ./env.sh
source ./sh/functions.sh

set -x

add_separator "CREATING LDAP POD"

# FIXME: use image and scripts from services team

if [ "$USE_PROVISIONING" = yes ]; then
  ldap_kind=symas
else
  ldap_kind=openldap
fi

if [ "$ldap_kind" = symas ]; then
  pull_images_for_pod k8s-blueprints/symas-pod.yaml
  delete_pod_if_exists  symas-pod
  kubectl apply -f k8s-blueprints/symas-pod.yaml
  wait_till_pod_is_Running  symas-pod
  add_separator SUCCESSFULLY CREATED SYMAS POD.
else

  # Creating 'manual' openldap pod.

  mkdir -p /var/lib/ldap
  echo "ldap:x:55:" >> /etc/group
  echo "ldap:x:55:55:OpenLDAP server:/var/lib/ldap:/sbin/nologin" >> /etc/passwd
  chown -R ldap.ldap /var/lib/ldap

  cat ./k8s-blueprints/openldap-pv.yaml.template \
    | sed "s/<vm-hostname>/${HOST_FQDN}/" \
    > ./k8s-blueprints/openldap-pv.yaml

  kubectl apply -f ./k8s-blueprints/openldap-pv.yaml

  # download images using docker -- 'kubectl init' is not able to apply user
  # credentials, and so is suffering from rate limits.
  pull_images_for_pod ./k8s-blueprints/openldap-stateful.yaml
  delete_pod_if_exists  openldap
  kubectl apply -f ./k8s-blueprints/openldap-stateful.yaml
  wait_till_pod_is_Running  openldap

  add_separator SUCCESSFULLY CREATED OPENLDAP POD
fi

set_var_SVC_IP openldap-svc
OPENLDAP_SVC="$SVC_IP"
echo "OPENLDAP_SVC='$OPENLDAP_SVC'" >> env.sh

if [ "$ldap_kind" = openldap ]; then
  yum install -y openldap-clients

  # apply .ldif files
  ldapadd -x -D "cn=admin,dc=seagate,dc=com" -w ldapadmin -f ldif/ldap-init.ldif -H "ldap://$OPENLDAP_SVC"
  ldapadd -x -D "cn=admin,dc=seagate,dc=com" -w ldapadmin -f ldif/iam-admin.ldif -H "ldap://$OPENLDAP_SVC"
  ldapmodify -x -a -D cn=admin,dc=seagate,dc=com -w ldapadmin -f ldif/ppolicy-default.ldif -H "ldap://$OPENLDAP_SVC"
fi

add_separator SUCCESSFULLY CREATED LDAP POD