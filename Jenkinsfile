#!groovy

pipeline {
    agent any
    environment {
        AGAVE_JOB_TIMEOUT = 900
        AGAVE_JOB_GET_DIR = "job_output"
        CONTAINER_REPO    = "validate_manifest"
        CONTAINER_TAG     = "test"
        REACTOR_LOCAL     = 1
        REACTOR_USE_TMP   = 0
        REACTOR_RUN_OPTS  = ""
        REACTOR_RC        = "reactor.rc"
        AGAVE_CACHE_DIR   = "${HOME}/credentials_cache/${JOB_BASE_NAME}"
        AGAVE_JSON_PARSER = "jq"
        AGAVE_TENANTID    = "sd2e"
        AGAVE_APISERVER   = "https://api.sd2e.org"
        AGAVE_USERNAME    = "sd2etest"
        AGAVE_PASSWORD    = credentials('sd2etest-tacc-password')
        REGISTRY_USERNAME = "sd2etest"
        REGISTRY_PASSWORD = credentials('sd2etest-dockerhub-password')
        REGISTRY_ORG      = credentials('sd2etest-dockerhub-org')
        PATH = "${HOME}/bin:${HOME}/sd2e-cloud-cli/bin:${env.PATH}"
        }
    stages {

        stage('Create Oauth client') {
            steps {
                sh "make-session-client ${JOB_BASE_NAME} ${JOB_BASE_NAME}-${BUILD_ID}"
            }
        }
        stage('Build container') {
            steps {
                sh "abaco deploy -R"
            }
        }
        stage('Run local tests') {
            steps {
                sh "make tests"
            }
        }
    }
    post {
        always {
           sh "delete-session-client ${JOB_BASE_NAME} ${JOB_BASE_NAME}-${BUILD_ID}"
        }
        success {
           deleteDir()
        }
    }
}
