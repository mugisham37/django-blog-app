# Kubernetes Deployment Makefile
# Provides convenient commands for managing Kubernetes deployments

# Default values
ENVIRONMENT ?= development
IMAGE_TAG ?= latest
TIMEOUT ?= 600
COMPONENT ?= all

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
CYAN := \033[0;36m
NC := \033[0m # No Color

# Helper functions
define log_info
	@echo "$(CYAN)[INFO]$(NC) $(1)"
endef

define log_success
	@echo "$(GREEN)[SUCCESS]$(NC) $(1)"
endef

define log_warning
	@echo "$(YELLOW)[WARNING]$(NC) $(1)"
endef

define log_error
	@echo "$(RED)[ERROR]$(NC) $(1)"
endef

.PHONY: help
help: ## Show this help message
	@echo "Kubernetes Deployment Management"
	@echo ""
	@echo "Usage: make [target] [ENVIRONMENT=env] [IMAGE_TAG=tag]"
	@echo ""
	@echo "Targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(CYAN)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "Examples:"
	@echo "  make deploy ENVIRONMENT=development"
	@echo "  make deploy ENVIRONMENT=production IMAGE_TAG=v1.2.3"
	@echo "  make rollback ENVIRONMENT=staging COMPONENT=django-api"
	@echo "  make test ENVIRONMENT=production"

.PHONY: check-env
check-env: ## Check if ENVIRONMENT is set
	@if [ -z "$(ENVIRONMENT)" ]; then \
		$(call log_error,"ENVIRONMENT is required. Use: make target ENVIRONMENT=development|staging|production"); \
		exit 1; \
	fi

.PHONY: check-tools
check-tools: ## Check if required tools are installed
	$(call log_info,"Checking required tools...")
	@command -v kubectl >/dev/null 2>&1 || { $(call log_error,"kubectl is required but not installed"); exit 1; }
	@command -v kustomize >/dev/null 2>&1 || { $(call log_error,"kustomize is required but not installed"); exit 1; }
	$(call log_success,"All required tools are available")

.PHONY: validate
validate: check-env check-tools ## Validate Kubernetes configuration
	$(call log_info,"Validating configuration for $(ENVIRONMENT) environment...")
	@if command -v pwsh >/dev/null 2>&1; then \
		pwsh ./scripts/validate.ps1 -Environment $(ENVIRONMENT); \
	else \
		$(call log_warning,"PowerShell not available, using basic validation"); \
		kustomize build overlays/$(ENVIRONMENT) | kubectl apply --dry-run=client -f -; \
	fi
	$(call log_success,"Configuration validation completed")

.PHONY: build
build: check-env ## Build Kubernetes manifests
	$(call log_info,"Building manifests for $(ENVIRONMENT) environment...")
	@mkdir -p build/$(ENVIRONMENT)
	@kustomize build overlays/$(ENVIRONMENT) > build/$(ENVIRONMENT)/manifests.yaml
	$(call log_success,"Manifests built: build/$(ENVIRONMENT)/manifests.yaml")

.PHONY: deploy
deploy: check-env check-tools validate ## Deploy to Kubernetes
	$(call log_info,"Deploying to $(ENVIRONMENT) environment with image tag $(IMAGE_TAG)...")
	@if command -v pwsh >/dev/null 2>&1; then \
		pwsh ./scripts/deploy.ps1 -Environment $(ENVIRONMENT) -ImageTag $(IMAGE_TAG) -Timeout $(TIMEOUT); \
	else \
		./scripts/deploy.sh -e $(ENVIRONMENT) -t $(IMAGE_TAG) --timeout $(TIMEOUT); \
	fi
	$(call log_success,"Deployment completed successfully")

.PHONY: deploy-dry-run
deploy-dry-run: check-env check-tools validate ## Perform dry run deployment
	$(call log_info,"Performing dry run deployment to $(ENVIRONMENT) environment...")
	@if command -v pwsh >/dev/null 2>&1; then \
		pwsh ./scripts/deploy.ps1 -Environment $(ENVIRONMENT) -ImageTag $(IMAGE_TAG) -DryRun; \
	else \
		./scripts/deploy.sh -e $(ENVIRONMENT) -t $(IMAGE_TAG) --dry-run; \
	fi
	$(call log_success,"Dry run completed")

.PHONY: rollback
rollback: check-env check-tools ## Rollback deployment
	$(call log_info,"Rolling back $(COMPONENT) in $(ENVIRONMENT) environment...")
	@if command -v pwsh >/dev/null 2>&1; then \
		pwsh ./scripts/rollback.ps1 -Environment $(ENVIRONMENT) -Component $(COMPONENT); \
	else \
		$(call log_error,"Rollback script requires PowerShell"); \
		exit 1; \
	fi
	$(call log_success,"Rollback completed")

.PHONY: test
test: check-env ## Test deployment health
	$(call log_info,"Testing deployment health for $(ENVIRONMENT) environment...")
	@if command -v pwsh >/dev/null 2>&1; then \
		pwsh ./scripts/test-deployment.ps1 -Environment $(ENVIRONMENT); \
	else \
		$(call log_warning,"PowerShell not available, using basic health checks"); \
		kubectl get pods -n fullstack-monolith-$(ENVIRONMENT); \
		kubectl get services -n fullstack-monolith-$(ENVIRONMENT); \
	fi
	$(call log_success,"Health tests completed")

.PHONY: status
status: check-env ## Show deployment status
	$(call log_info,"Checking deployment status for $(ENVIRONMENT) environment...")
	@NAMESPACE=$$(case $(ENVIRONMENT) in \
		development) echo "fullstack-monolith-dev" ;; \
		staging) echo "fullstack-monolith-staging" ;; \
		production) echo "fullstack-monolith-prod" ;; \
		*) echo "fullstack-monolith-$(ENVIRONMENT)" ;; \
	esac); \
	echo "Namespace: $$NAMESPACE"; \
	echo ""; \
	echo "Pods:"; \
	kubectl get pods -n $$NAMESPACE; \
	echo ""; \
	echo "Services:"; \
	kubectl get services -n $$NAMESPACE; \
	echo ""; \
	echo "Ingresses:"; \
	kubectl get ingresses -n $$NAMESPACE; \
	echo ""; \
	echo "HPA Status:"; \
	kubectl get hpa -n $$NAMESPACE

.PHONY: logs
logs: check-env ## Show application logs
	$(call log_info,"Showing logs for $(ENVIRONMENT) environment...")
	@NAMESPACE=$$(case $(ENVIRONMENT) in \
		development) echo "fullstack-monolith-dev" ;; \
		staging) echo "fullstack-monolith-staging" ;; \
		production) echo "fullstack-monolith-prod" ;; \
		*) echo "fullstack-monolith-$(ENVIRONMENT)" ;; \
	esac); \
	PREFIX=$$(case $(ENVIRONMENT) in \
		development) echo "dev-" ;; \
		staging) echo "staging-" ;; \
		production) echo "prod-" ;; \
		*) echo "$(ENVIRONMENT)-" ;; \
	esac); \
	echo "Django API logs:"; \
	kubectl logs -f deployment/$${PREFIX}django-api -n $$NAMESPACE --tail=50

.PHONY: scale
scale: check-env ## Scale deployment (usage: make scale ENVIRONMENT=prod COMPONENT=django-api REPLICAS=5)
	$(call log_info,"Scaling $(COMPONENT) to $(REPLICAS) replicas in $(ENVIRONMENT) environment...")
	@NAMESPACE=$$(case $(ENVIRONMENT) in \
		development) echo "fullstack-monolith-dev" ;; \
		staging) echo "fullstack-monolith-staging" ;; \
		production) echo "fullstack-monolith-prod" ;; \
		*) echo "fullstack-monolith-$(ENVIRONMENT)" ;; \
	esac); \
	PREFIX=$$(case $(ENVIRONMENT) in \
		development) echo "dev-" ;; \
		staging) echo "staging-" ;; \
		production) echo "prod-" ;; \
		*) echo "$(ENVIRONMENT)-" ;; \
	esac); \
	kubectl scale deployment $${PREFIX}$(COMPONENT) --replicas=$(REPLICAS) -n $$NAMESPACE
	$(call log_success,"Scaling completed")

.PHONY: restart
restart: check-env ## Restart deployment
	$(call log_info,"Restarting $(COMPONENT) in $(ENVIRONMENT) environment...")
	@NAMESPACE=$$(case $(ENVIRONMENT) in \
		development) echo "fullstack-monolith-dev" ;; \
		staging) echo "fullstack-monolith-staging" ;; \
		production) echo "fullstack-monolith-prod" ;; \
		*) echo "fullstack-monolith-$(ENVIRONMENT)" ;; \
	esac); \
	PREFIX=$$(case $(ENVIRONMENT) in \
		development) echo "dev-" ;; \
		staging) echo "staging-" ;; \
		production) echo "prod-" ;; \
		*) echo "$(ENVIRONMENT)-" ;; \
	esac); \
	if [ "$(COMPONENT)" = "all" ]; then \
		kubectl rollout restart deployment -n $$NAMESPACE; \
	else \
		kubectl rollout restart deployment/$${PREFIX}$(COMPONENT) -n $$NAMESPACE; \
	fi
	$(call log_success,"Restart completed")

.PHONY: port-forward
port-forward: check-env ## Port forward services (usage: make port-forward ENVIRONMENT=dev)
	$(call log_info,"Setting up port forwarding for $(ENVIRONMENT) environment...")
	@NAMESPACE=$$(case $(ENVIRONMENT) in \
		development) echo "fullstack-monolith-dev" ;; \
		staging) echo "fullstack-monolith-staging" ;; \
		production) echo "fullstack-monolith-prod" ;; \
		*) echo "fullstack-monolith-$(ENVIRONMENT)" ;; \
	esac); \
	PREFIX=$$(case $(ENVIRONMENT) in \
		development) echo "dev-" ;; \
		staging) echo "staging-" ;; \
		production) echo "prod-" ;; \
		*) echo "$(ENVIRONMENT)-" ;; \
	esac); \
	echo "Starting port forwarding..."; \
	echo "Django API: http://localhost:8000"; \
	echo "Next.js Web: http://localhost:3000"; \
	echo "Press Ctrl+C to stop"; \
	kubectl port-forward service/$${PREFIX}django-api-service 8000:8000 -n $$NAMESPACE & \
	kubectl port-forward service/$${PREFIX}nextjs-web-service 3000:3000 -n $$NAMESPACE & \
	wait

.PHONY: clean
clean: check-env ## Clean up deployment
	$(call log_warning,"Cleaning up $(ENVIRONMENT) environment...")
	@NAMESPACE=$$(case $(ENVIRONMENT) in \
		development) echo "fullstack-monolith-dev" ;; \
		staging) echo "fullstack-monolith-staging" ;; \
		production) echo "fullstack-monolith-prod" ;; \
		*) echo "fullstack-monolith-$(ENVIRONMENT)" ;; \
	esac); \
	read -p "Are you sure you want to delete all resources in $$NAMESPACE? (y/N): " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		kubectl delete all --all -n $$NAMESPACE; \
		kubectl delete pvc --all -n $$NAMESPACE; \
		kubectl delete secrets --all -n $$NAMESPACE; \
		kubectl delete configmaps --all -n $$NAMESPACE; \
	else \
		echo "Cleanup cancelled"; \
	fi

.PHONY: setup-dev
setup-dev: ## Setup development environment
	$(call log_info,"Setting up development environment...")
	@make deploy ENVIRONMENT=development IMAGE_TAG=dev-latest
	@make port-forward ENVIRONMENT=development &
	$(call log_success,"Development environment ready")

.PHONY: setup-staging
setup-staging: ## Setup staging environment
	$(call log_info,"Setting up staging environment...")
	@make deploy ENVIRONMENT=staging IMAGE_TAG=staging-latest
	$(call log_success,"Staging environment ready")

.PHONY: promote-to-prod
promote-to-prod: ## Promote staging to production (usage: make promote-to-prod IMAGE_TAG=v1.2.3)
	$(call log_warning,"Promoting to production with image tag $(IMAGE_TAG)...")
	@read -p "Are you sure you want to deploy $(IMAGE_TAG) to production? (y/N): " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		make deploy ENVIRONMENT=production IMAGE_TAG=$(IMAGE_TAG); \
		make test ENVIRONMENT=production; \
	else \
		echo "Production deployment cancelled"; \
	fi

.PHONY: backup
backup: check-env ## Backup configuration and data
	$(call log_info,"Creating backup for $(ENVIRONMENT) environment...")
	@NAMESPACE=$$(case $(ENVIRONMENT) in \
		development) echo "fullstack-monolith-dev" ;; \
		staging) echo "fullstack-monolith-staging" ;; \
		production) echo "fullstack-monolith-prod" ;; \
		*) echo "fullstack-monolith-$(ENVIRONMENT)" ;; \
	esac); \
	BACKUP_DIR="backups/$(ENVIRONMENT)/$$(date +%Y%m%d-%H%M%S)"; \
	mkdir -p $$BACKUP_DIR; \
	kubectl get all,pvc,secrets,configmaps -n $$NAMESPACE -o yaml > $$BACKUP_DIR/resources.yaml; \
	kubectl get pv -o yaml > $$BACKUP_DIR/persistent-volumes.yaml
	$(call log_success,"Backup created in $$BACKUP_DIR")

.PHONY: restore
restore: check-env ## Restore from backup (usage: make restore ENVIRONMENT=dev BACKUP_DIR=backups/dev/20231201-120000)
	$(call log_warning,"Restoring $(ENVIRONMENT) environment from $(BACKUP_DIR)...")
	@if [ -z "$(BACKUP_DIR)" ]; then \
		$(call log_error,"BACKUP_DIR is required"); \
		exit 1; \
	fi; \
	if [ ! -f "$(BACKUP_DIR)/resources.yaml" ]; then \
		$(call log_error,"Backup file not found: $(BACKUP_DIR)/resources.yaml"); \
		exit 1; \
	fi; \
	read -p "Are you sure you want to restore from $(BACKUP_DIR)? This will overwrite existing resources. (y/N): " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		kubectl apply -f $(BACKUP_DIR)/persistent-volumes.yaml; \
		kubectl apply -f $(BACKUP_DIR)/resources.yaml; \
	else \
		echo "Restore cancelled"; \
	fi

.PHONY: update-secrets
update-secrets: check-env ## Update secrets interactively
	$(call log_info,"Updating secrets for $(ENVIRONMENT) environment...")
	@NAMESPACE=$$(case $(ENVIRONMENT) in \
		development) echo "fullstack-monolith-dev" ;; \
		staging) echo "fullstack-monolith-staging" ;; \
		production) echo "fullstack-monolith-prod" ;; \
		*) echo "fullstack-monolith-$(ENVIRONMENT)" ;; \
	esac); \
	echo "Current secrets:"; \
	kubectl get secrets -n $$NAMESPACE; \
	echo ""; \
	read -p "Enter secret name to update: " secret_name; \
	read -p "Enter key to update: " key; \
	read -s -p "Enter new value: " value; \
	echo ""; \
	kubectl patch secret $$secret_name -p "{\"data\":{\"$$key\":\"$$(echo -n $$value | base64)\"}}" -n $$NAMESPACE
	$(call log_success,"Secret updated successfully")

.PHONY: monitor
monitor: check-env ## Monitor deployment metrics
	$(call log_info,"Monitoring $(ENVIRONMENT) environment...")
	@NAMESPACE=$$(case $(ENVIRONMENT) in \
		development) echo "fullstack-monolith-dev" ;; \
		staging) echo "fullstack-monolith-staging" ;; \
		production) echo "fullstack-monolith-prod" ;; \
		*) echo "fullstack-monolith-$(ENVIRONMENT)" ;; \
	esac); \
	watch -n 5 "kubectl top pods -n $$NAMESPACE && echo '' && kubectl get hpa -n $$NAMESPACE"

.PHONY: debug
debug: check-env ## Debug deployment issues
	$(call log_info,"Debugging $(ENVIRONMENT) environment...")
	@NAMESPACE=$$(case $(ENVIRONMENT) in \
		development) echo "fullstack-monolith-dev" ;; \
		staging) echo "fullstack-monolith-staging" ;; \
		production) echo "fullstack-monolith-prod" ;; \
		*) echo "fullstack-monolith-$(ENVIRONMENT)" ;; \
	esac); \
	echo "Pod Status:"; \
	kubectl get pods -n $$NAMESPACE; \
	echo ""; \
	echo "Events:"; \
	kubectl get events --sort-by=.metadata.creationTimestamp -n $$NAMESPACE | tail -10; \
	echo ""; \
	echo "Failed Pods:"; \
	kubectl get pods -n $$NAMESPACE --field-selector=status.phase=Failed; \
	echo ""; \
	echo "Resource Usage:"; \
	kubectl top pods -n $$NAMESPACE 2>/dev/null || echo "Metrics server not available"

# Default target
.DEFAULT_GOAL := help