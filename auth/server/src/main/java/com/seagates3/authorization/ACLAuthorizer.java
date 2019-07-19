/*
 * COPYRIGHT 2019 SEAGATE LLC
 *
 * THIS DRAWING/DOCUMENT, ITS SPECIFICATIONS, AND THE DATA CONTAINED
 * HEREIN, ARE THE EXCLUSIVE PROPERTY OF SEAGATE TECHNOLOGY
 * LIMITED, ISSUED IN STRICT CONFIDENCE AND SHALL NOT, WITHOUT
 * THE PRIOR WRITTEN PERMISSION OF SEAGATE TECHNOLOGY LIMITED,
 * BE REPRODUCED, COPIED, OR DISCLOSED TO A THIRD PARTY, OR
 * USED FOR ANY PURPOSE WHATSOEVER, OR STORED IN A RETRIEVAL SYSTEM
 * EXCEPT AS ALLOWED BY THE TERMS OF SEAGATE LICENSES AND AGREEMENTS.
 *
 * YOU SHOULD HAVE RECEIVED A COPY OF SEAGATE'S LICENSE ALONG WITH
 * THIS RELEASE. IF NOT PLEASE CONTACT A SEAGATE REPRESENTATIVE
 * http://www.seagate.com/contact
 *
 * Original author:  Ajinkya Dhumal
 * Original creation date: 05-July-2019
 */

package com.seagates3.authorization;

import java.io.IOException;
import java.util.Map;

import javax.xml.parsers.ParserConfigurationException;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.xml.sax.SAXException;

import com.seagates3.exception.BadRequestException;
import com.seagates3.exception.GrantListFullException;
import com.seagates3.model.Requestor;
import com.seagates3.util.ACLPermissionUtil;

import io.netty.handler.codec.http.HttpMethod;

public
class ACLAuthorizer {

 private
  final Logger LOGGER = LoggerFactory.getLogger(ACLAuthorizer.class.getName());

  /**
   * Evaluates the request with the attached ACL and returns true if the
   * operation is authorized
   * @param requestor
   * @param requestBody
   * @return - true if Principal is authorized to perform requested operation
   * @throws ParserConfigurationException
   * @throws SAXException
   * @throws IOException
   * @throws BadRequestException
   * @throws GrantListFullException
   */
  boolean isAuthorized(Requestor requestor, Map<String, String> requestBody)
      throws ParserConfigurationException,
      SAXException, IOException, BadRequestException, GrantListFullException {

    // TODO Temporary implementation. Need to check the scenario where a
    // create-bucket is requested which will not have ACL initially
    if (requestBody.get("acp") == null) {
      String ex = "Bad request. Resource ACL absent in the request.";
      LOGGER.error(ex);
      throw new BadRequestException(ex);
    }

    AccessControlPolicy acl = new AccessControlPolicy(requestBody.get("acp"));
    String method = requestBody.get("Method");
    if (method == null || method.isEmpty()) {
      String ex = "Invalid HTTP method: " + method;
      LOGGER.error(ex);
      throw new BadRequestException(ex);
    }
    HttpMethod httpMethod = HttpMethod.valueOf(method);

    String requiredPermission = ACLPermissionUtil.getACLPermission(
        httpMethod, requestBody.get("ClientAbsoluteUri"));
    if (requiredPermission == null) {
      String ex = "Bad request. HTTP method or Permission unknown.";
      LOGGER.error(ex);
      throw new BadRequestException(ex);
    }

    if (requestor != null) {
      String canonicalId = requestor.getAccount().getCanonicalId();
      Grant grant = acl.getAccessControlList().getGrant(canonicalId);

      if (grant == null) {
        LOGGER.debug("No Grants found in ACL for Canonical id: " + canonicalId);
        return false;
      }

      String permissionGrant = grant.getPermission();
      if ("FULL_CONTROL".equals(permissionGrant) ||
          requiredPermission.equals(permissionGrant)) {
        return true;
      } else if (canonicalId.equals(acl.getOwner().getCanonicalId()) &&
                 ("READ_ACP".equals(requiredPermission) ||
                  "WRITE_ACP".equals(requiredPermission))) {
        return true;
      } else {
        return false;
      }

    } else {
      // TODO: Code for Groups and Roles
      return false;  // temporary, till this part is implemented
    }
  }
}
