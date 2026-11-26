pipeline {
    agent any
    stages {
        stage('Construccion') {
            steps {
                sh 'docker build -t app-securedev:latest .'
            }
        }
        stage('Despliegue Pruebas') {
            steps {
                sh 'docker rm -f app-test || true'
                sh 'docker run -d --name app-test --network devsecops-net -p 5001:5000 app-securedev:latest'
                sh 'sleep 5'
            }
        }
        stage('Pruebas Seguridad OWASP ZAP') {
            steps {
                sh '''
                docker run --rm --network devsecops-net -v $(pwd):/zap/wrk/:rw \
                ghcr.io/zaproxy/zaproxy:stable zap-baseline.py \
                -t http://app-test:5000 -r reporte_zap.html || true
                '''
            }
        }
        stage('Despliegue Produccion') {
            steps {
                sh 'docker rm -f app-prod || true'
                sh 'docker run -d --name app-prod --network devsecops-net -p 5000:5000 app-securedev:latest'
            }
        }
    }
    post {
        always {
            archiveArtifacts artifacts: 'reporte_zap.html', allowEmptyArchive: true
        }
    }
}
