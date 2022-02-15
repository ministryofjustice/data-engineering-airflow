package k8spspallowprivilegeescalationcontainer

# Prevent pods from running if any containers or init containers have
# allowPrivilegeEscalation set to true

violation[{"msg": msg, "details": {}}] {
	container := input_containers[_]
	non_compliant_containers := [container | allow_privilege_escalation(container)]
	count(non_compliant_containers) > 0
	msg := "Privilege escalation is not allowed."
}

allow_privilege_escalation(container) {
	container.securityContext.allowPrivilegeEscalation
	not container.securityContext.allowPrivilegeEscalation == false
}

input_containers[container] {
	container := input.review.object.spec.containers[_]
}

input_containers[container] {
	container := input.review.object.spec.initContainers[_]
}
