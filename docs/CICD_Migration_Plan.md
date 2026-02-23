# Migration Plan: Jenkins to Inka CI/CD Control Center

## 1. Inventory & Analysis
- Export all `Jenkinsfile` configurations from existing jobs.
- Map Jenkins plugins to GCP/Inka equivalents:
    - `Gerrit/GitHub Trigger` -> Inka Webhook Listener.
    - `Pipeline: Nodes` -> Cloud Build Worker Pools.
    - `Credentials Binding` -> Secret Manager integration.
    - `Blue Ocean UI` -> Inka Dashboard.

## 2. Pipeline Translation
Convert `Jenkinsfile` (Groovy) to `pipeline.yaml` (Inka Spec).
Example:
**Jenkinsfile**:
```groovy
pipeline {
    agent any
    stages {
        stage('Build') { steps { sh 'npm run build' } }
    }
}
```
**Inka pipeline.yaml**:
```yaml
name: my-app
stages:
  - name: Build
    type: cloud-build
    config:
      build_config: cloudbuild.yaml
```

## 3. Phased Migration
1. **Parallel Run**: Keep Jenkins running as the primary deployer while Inka Control Center runs in "shadow mode" (building but not deploying).
2. **Dev Shift**: Migrate Dev deployments to the Control Center.
3. **Staging Shift**: Migrate Staging and verify approval gates.
4. **Prod Cutover**: Final cutover to Inka for Production deployments.

## 4. Rollback Strategy
Maintain Jenkins jobs for 30 days post-migration to allow emergency fallback if the Control Center encounters critical issues.
