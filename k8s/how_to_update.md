Push new versions of containers

oc scale --replicas=2 deployment/prism-api
oc delete pods <old_pod_name>
oc scale --replicas=1 deployment/prism-api
oc get pods --field-selector 'status.phase==Failed' -o json | oc delete -f -
