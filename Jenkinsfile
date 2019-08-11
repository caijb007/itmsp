pipeline {
  agent {
    docker {
      image 'django: 1.10.4-python2'
      args '-p 9001:9001'
    }

  }
  stages {
    stage('Build') {
      steps {
        sh '''yum install pip
'''
        sh 'yum insall python-devel'
      }
    }
  }
}