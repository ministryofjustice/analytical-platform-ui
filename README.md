# Analytical Platform UI

[![Ministry of Justice Repository Compliance Badge](https://github-community.service.justice.gov.uk/repository-standards/api/analytical-platform-ui/badge)](https://github-community.service.justice.gov.uk/repository-standards/analytical-platform-ui)

## Running Locally

The app can be run in a DevContainer via Docker. The DevContainer Visual Studio Code extension is recommended, as is Docker Desktop.

For more information on Dev Containers, see the [Analytical Platform docs.](https://technical-documentation.data-platform.service.justice.gov.uk/documentation/platform/infrastructure/developing.html#developing-the-data-platform)

Python dependencies are installed and managed by [`uv`](https://docs.astral.sh/uv/). See the `uv` documentation for information about running commands with `uv`.

### Building the DevContainer

To build the dev container, ensure Docker desktop is running, then open the AP UI project in Visual Studio Code. Open the command pallet by hitting command+shift+p and search for `Dev Containers: Reopen in container` and hit enter. This will build the dev container.

If you are using a workspace with multiple applications, search for `Dev Containers: Open folder in Container…` instead, then select the AP UI folder. Once the dev container has finished building, it should install all the required Python and npm dependencies, as well as run the migrations.

### Environment Variables

There is an example environment file stored on 1Password named `Analytical Platform UI Env`. Paste the contents into a new file called `.env` in the root of the project.

If you have the 1password CLI installed on your local machine, you use the following command to copy the file:

```bash
op document get --vault "Analytical Platform" "Analytical Platform UI .env" --out-file .env
```

For installation instructions for the 1password CLI see [the documentation here](https://developer.1password.com/docs/cli/get-started/).

### Running Development Server

To run the server, you will need to use aws-sso cli. To find the correct profile, run `aws-sso list` in the terminal. This will provide you with a link to sign in via SSO. Once signed in, a list of profiles will be displayed. You are looking for the profile name linked to the `analytical-platform-compute-development` AccountAlias.

To run the server using this profile, enter `aws-sso exec --profile analytical-platform-compute-development:modernisation-platform-sandbox -- python manage.py runserver` or `make serve-sso`. Then go to `localhost:8000` and sign in using your @justice.gov.uk identity.

### Local debugging

Copy `launch.json.example`, `settings.json.example` and `tasks.json.example` from the examples folder into a `.vscode` folder in the root of the project and remove the `.example` suffix. To debug the application, go to the `run and debug` tab and select the `runserver` configuration. When starting debugging you may need to sign into AWS first. There will be a prompt in the terminal to do so.

To debug any tests, switch the debug configuration to `Python: Debug Tests` then go to the testing tab. From here you can run the full suite of tests or individual tests. You can also click the debug icon in order to debug any tests that are failing.

### Updating Migrations

To run the migrations locally, run `python manage.py migrate` in the terminal.

### Updating static assets

To build the static assets, run `make build-static` in the terminal.

## Release Procedure

To create a release of the Analytical Platform UI:

- Before merging your branch to main, bump both the `version` and `appVersion` in `chart/Chart.yaml`
  - We use SemVer without a v prefix, e.g `1.0.0`
  - Release candidates are specified with a `-rcX` postfix, e.g `1.0.0-rc1`
- Once changes have been merged, go to the repository in GitHub.
- Go to releases and click the Draft a new release button
- Click choose a tag and specify the version you set in `chart/Chart.yaml` and click create new tag
- Click generate release notes, click set as prerelease if the branch is a release candidate
- Click publish release. This will build the image and push the helm chart
- Once the build has finished, go to the modernisation-platform-environments repository. (You may need to [pull this down](https://github.com/ministryofjustice/modernisation-platform-environments) if you haven't previously)
- Create a new branch from main and go to `terraform/environments/analytical-platform-compute/helm-charts-applications.tf`
- Update the version to your new release version
- Commit the change and create a pull request
- Go to the pull request page and view the details of a running terraform plan (development, test or production are fine)
- If the development and test plans are successful, run the terraform apply on those environments
  - Do this by clicking apply under plan in the sidebar
  - Click `Review pending deployments` in the main panel
  - Tick the environments and click Approve and Deploy
- Once the apply job has finished, test changes in either region
- When you're happy with your changes, get the PR reviewed by another member of the team
- Merge your PR to main then go to actions and find the workflow running on main that is running the terraform plan
- Once the plan for production has finished, run the terraform apply job for production

## Environment Variables and Secrets

### Adding Environment Variables

Environment variables for the AP UI are specified in `charts/values.yaml` under app -> environment.
Any non-secret values can be added like the example below:

```yaml
app:
   environment:
      - name: DJANGO_SETTINGS_MODULE
      value: ap.settings
      - name: NEW_VAR_NAME
      value: new_var_value
```

Create a pull request and follow the release process and your new environment variable should be accessible.

### Adding Secrets

There are a 2 of types of secrets that can be added:

- Kubernetes Secrets
- External Secrets

Both are created through the modernisation-platform-environments repository then referenced in `charts/values.yaml`.

#### Kubernetes Secrets

Todo later as I don't know the whats or whys

#### External Secrets

External secrets are held in AWS Secrets Manager.

To add an external secret:

- Go to the modernisation-platform-environments repository and create a new branch
- navigate to `terraform/environments/analytical-platform-compute/secrets.tf`
- add a new block that looks like the example below (change the sections marked with <>)
  - Keep the secret_string as CHANGEME as this will be changed in Secrets Manager

```tf
module "<secret_module_name>" {
  #checkov:skip=CKV_TF_1:Module registry does not support commit hashes for versions
  #checkov:skip=CKV_TF_2:Module registry does not support tags for versions

  source  = "terraform-aws-modules/secrets-manager/aws"
  version = "1.1.2"

  name        = "ui/<name_here>"
  description = "<description here>"
  kms_key_id  = module.common_secrets_manager_kms.key_arn

  secret_string         = "CHANGEME"
  ignore_secret_changes = true

  tags = local.tags
}
```

- Commit and push the changes
  - Create a PR and follow the same process to release these changes in test and development as you would deploying the application.
  - Read the [Release Procedure](#release-procedure) section if you're unsure.
- Go to the AWS console and log into either the Analytical-Platform-Compute-Development or Analytical-Platform-Compute-Test account
- Go to Secrets Manager
- If the terraform apply was successful, you should see your new secret here
- Click on the secret name then click Retrieve Secret Value (You should see CHANGEME)
- Click edit
  - Modify the value to what you want the secret to be
  - Click save
- Get the PR approved, merged to main and apply the changes to production
- Once the secret is in production, change it in secrets manager in Analytical-Platform-Compute-Production then create a new branch in modernisation-platform-environments repository
- Navigate to `terraform/environments/analytical-platform-compute/kubernetes-external-secrets.tf`
- Add a block that looks similar to the example below (change the sections marked with <>)

```tf
resource "kubernetes_manifest" "<external_secret_name>" {
 manifest = {
   "apiVersion" = "external-secrets.io/v1beta1"
   "kind"       = "ExternalSecret"
   "metadata" = {
     "name"      = "ui-<secret-name>"
     "namespace" = kubernetes_namespace.ui.metadata[0].name
   }
   "spec" = {
     "secretStoreRef" = {
       "kind" = "ClusterSecretStore"
       "name" = "aws-secretsmanager"
     }
     "target" = {
       "name" = "ui-<secret-name>" # should be the same as the metadata name
     }
     "data" = [  # you could have multiple related secrets in this block
       {
         "remoteRef" = {
           "key" = module.<secret_module_create_above_name_here>.secret_id
         }
         "secretKey" = "<key-name-here>"
       }
     ]
   }
 }
}
```

- Follow the same process above to add this to the dev/test/prod.
- Once the secrets have been added, create a new branch in this repository and go to `charts/values.yaml` and add a block like the example below

```yaml
- name: EXTERNAL_SECRET_NAME
     valueFrom:
       secretKeyRef:
         name: <target-name>
         key: <secretKey>
```

- name references the `name` in the `target` block in the second example
- key references the `secretKey` in the `data` block in the second example
- create a PR and follow the release process. The new secret should get picked up in the environment.
