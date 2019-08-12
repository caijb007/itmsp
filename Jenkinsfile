pipeline {
  agent {
    docker {
      args '-p 9001:9001'
      image 'django:1.10.4-python2'
    }

  }
  stages {
    stage('Build') {
      steps {
        sh 'pip install -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt'
      }
    }
  }
}