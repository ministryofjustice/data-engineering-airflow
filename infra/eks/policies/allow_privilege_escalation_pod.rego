package k8spspallowprivilegeescalationpod

# Prevent pods from running if they do not have allowPrivilegeEscalation set to false
# in the security context

violation[{"msg": msg, "details": {}}] {
	allow_privilege_escalation(input.review.object)
	msg := sprintf("Privilege escalation is not allowed. %v", input)
}

allow_privilege_escalation(pod) {
	not pod.spec.securityContext.allowPrivilegeEscalation == false
}
