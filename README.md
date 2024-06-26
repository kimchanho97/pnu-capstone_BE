# 클라우드 배포를 위한 쿠버네티스 플랫폼: 개발자 통합 배포 관리 솔루션

> 부산대학교 정보컴퓨터공학부 2023후기 졸업과제 - 척척학사팀

### 목차

1. [프로젝트 소개](#1-프로젝트-소개)
2. [팀원 소개](#2-팀원-소개)
3. [링크 모음](#3-링크-모음)
4. [개발 환경](#4-개발-환경)
5. [시스템 구성도](#5-시스템-구성도)
6. [플랫폼 소개](#6-플랫폼-소개)
7. [ERD](#7-erd)

<br>

## 1. 프로젝트 소개

### 연구 배경과 기존 문제점

현대 소프트웨어 개발 환경에서는 빠르고 안정적인 배포가 필수적입니다. 그러나 CI/CD 파이프라인을 구축하고 운영하는 데는 많은 노력과 전문 지식이 필요합니다. 특히, 쿠버네티스와 같은 컨테이너 오케스트레이션 기술을 사용하면 더욱 복잡해집니다. 

+ **쿠버네티스 기반 배포의 복잡성**: 쿠버네티스 클러스터에 컨테이너 이미지를 배포하고, 다양한 Kubernetes 리소스를 정의하고 관리해야 하며, 네트워킹, 스토리지, 보안 설정 등을 포함한 복잡한 환경 설정이 필요합니다. 이는 높은 러닝 커브와 부담을 요구합니다.
+ **초기 단계의 CI/CD 구축 어려움**: CI/CD 파이프라인 구축에는 높은 학습 부담과 운영 비용이 필요합니다. 수동 작업에 의존하는 기존의 소프트웨어 배포 과정은 자동화 수준이 낮아 오류 발생 가능성이 높고, 개발 속도를 저해합니다.
+ **온프레미스와 클라우드 환경 연동의 복잡성**: 온프레미스 환경과 퍼블릭 클라우드를 연동하는 작업에는 많은 시간과 노력이 필요합니다. 네트워크 설정, 보안 구성 등의 복잡한 작업이 포함되며, 이를 효과적으로 관리하기 위해서는 기술적 전문 지식이 필요합니다.

<br>

### 서비스 소개 및 목적

본 프로젝트는 이러한 문제를 해결하기 위해 개발되었습니다. 개발자들이 CI/CD 파이프라인을 통해 소프트웨어를 자동화된 방식으로 배포하고 빠른 피드백을 받을 수 있도록 돕는 것을 목표로 합니다. 이를 위해 사용자 인증, 프로젝트 생성, 지속적인 통합 및 배포, 롤백 기능 등을 제공하는 클라우드 기반 쿠버네티스 플랫폼을 개발했습니다. 이 플랫폼은 개발자들이 CI/CD 파이프라인을 쉽고 효율적으로 활용할 수 있도록 지원합니다.

+ **신속한 빌드와 배포**: CI/CD 파이프라인 생성을 자동화하여 개발자들이 코드 변경 사항을 빠르게 빌드 및 배포하여 개발 효율성을 향상시킵니다.
+ **안정적인 배포 및 롤백**: 블루그린 배포 전략과 배포 기록 관리를 통해 배포 오류를 최소화하고 신속한 롤백이 가능합니다.
+ **확장성 및 가용성 제고**: 온프레미스와 클라우드 환경을 연계하여 자원을 효율적으로 사용하고 클라우드 버스팅으로 확장성과 가용성을 확보합니다.
+ **향상된 보안성**: GitHub 인증과 클라우드 VPN 연결을 통해 사용자 인증 및 온프레미스와 클라우드 간 통신 보안을 강화합니다.

<br>

## 2. 팀원 소개

|**이름**|**Github**| **역할**                                                                                                                                                                                                                                                           |
|:---:|:---:|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **김찬호** | <img src="https://github.com/kimchanho97.png" width="100" align="center"> <br> https://github.com/kimchanho97 | • 서비스 기획 및 설계 <br> • 화면 설계 및 유저 플로우 정의 <br> • REST API 정의 <br> • UI 구현 <br> • FE &#183; BE API 구현 <br> • 백엔드 프로젝트 설계 <br> • DB 모델링 <br> • DB 마이그레이션 관리 <br> • DB 인스턴스 배포 &#183; 연결 |
| **구성현** | <img src="https://github.com/qkoo0833.png" width="100" align="center"> <br> https://github.com/qkoo0833 | • Kubernetes 클러스터 설정 및 관리 <br> • CI/CD 파이프라인 리소스 구성 <br> • 클라우드 버스팅 구현 <br> • Helm 배포 지원 <br> • 블루그린 무중단 배포 <br> • 인프라스트럭처 코드화 <br> • 모니터링 적용 <br> • 인증서 자동관리 적용 <br> • DNS 발급 로직 개발 <br> • 빌드, 배포 태스크 개발 |            |


<br>

## 3. 링크 모음

+ https://pitapat.ne.kr/ (배포 중지 상태)
+ [API 문서](https://atlantic-apparel-5c0.notion.site/APIs-88828d18ad03402e86b49d98e7580078)
+ [FE 저장소](https://github.com/kimchanho97/capstone-frontend)
+ [BE 저장소](https://github.com/kimchanho97/capstone-backend)
+ [시연 영상](https://www.youtube.com/watch?v=FnXrIzA6jRs)
+ [연구 보고서](https://github.com/kimchanho97/capstone-frontend/blob/main/docs/2023%ED%9B%84%EA%B8%B0%20%EC%B5%9C%EC%A2%85%EB%B3%B4%EA%B3%A0%EC%84%9C_4_%EC%B2%99%EC%B2%99%ED%95%99%EC%82%AC_%ED%81%B4%EB%9D%BC%EC%9A%B0%EB%93%9C%EB%B0%B0%ED%8F%AC%EB%A5%BC%EC%9C%84%ED%95%9C%EC%BF%A0%EB%B2%84%EB%84%A4%ED%8B%B0%EC%8A%A4%ED%94%8C%EB%9E%AB%ED%8F%BC%20.pdf)

<br>

## 4. 개발 환경

| 분야                        | 사용 기술 및 도구                                     | 
|:---------------------------:|------------------------------------------------------| 
| **Infra** | • Kubernetes 1.28.1 <br> • Argo CD 2.10.2 <br> • Argo Rollouts 1.6.6 <br> • Argo Workflows 3.4.4 <br> • Argo Events 1.7.5 <br> • Ingress-nginx 1.5.1 <br> • Cert-manager 1.11.0  |
| **FrontEnd** | • React 18.2.0 <br> • Axios 1.6.8 <br> • TailwindCSS 3.4.1 <br> • @mui/material 5.15.15 <br> • React-Query 3.39.3 <br> • React-Router-DOM 6.22.3 <br> • Jotai 2.7.1|
| **BackEnd** | • Flask 3.0.3 <br> • Flask-Cors 4.0.0 <br> •Flask-Migrate 4.0.7 <br> • Flask-SQLAlchemy 2.0.30 <br> • Gunicorn 22.0.0 <br> • MySQLclient 2.2.4 <br> • Redis 5.0.4 <br> • Requests 2.31.0 |
| **DataBase** | • MySQL 8.0.35 |

<br>

## 5. 시스템 구성도

|전체 구성도|
|:---:|
|<img width="700" alt="image" src="https://github.com/kimchanho97/capstone-frontend/assets/104095041/5539bfba-c6af-4059-a225-4b6b46885594">|

- **쿠버네티스를 통한 자동화 및 리소스 관리 최적화**: 쿠버네티스를 활용하여 컨테이너의 자동 배포, 확장 및 관리가 이루어집니다.
- **통합된 개발 플랫폼 제공**: 웹 기반 인터페이스를 통해 사용자는 프로젝트 생성, 빌드, 배포 및 롤백을 진행할 수 있으며, Argo를 활용한 워크플로우 관리와 지속적인 배포(CD)가 가능합니다.
- **NGINX를 이용한 리버스 프록시**: Ingress NGINX를 활용하여 단일 IP 주소로 들어오는 트래픽을 서브도메인 별로 효과적으로 라우팅합니다.
- **향상된 운영을 위한 모니터링 제공**: Grafana와 Prometheus를 통해 실시간 모니터링과 데이터 시각화를 제공합니다.
- **Terraform을 통한 인프라 자동화**: Terraform을 사용하여 클라우드 리소스의 프로비저닝과 관리를 자동화합니다.

<br>
<br>

|CI / CD 파이프라인|
|:---:|
|<img width="700" alt="image" src="https://github.com/kimchanho97/capstone-frontend/assets/104095041/8819fc9d-ba12-4946-b2f1-9270bbad6204">|

- **자동화 및 안정성 강화된 CI/CD**: Argo Workflows와 GitHub Container Registry를 사용하여 컨테이너 빌드를 자동화하고, Argo Rollouts와 Helm을 활용한 블루-그린 배포로 고도의 안정성을 확보하며 신속한 롤백을 가능하게 한다.

<br>
<br>

|클라우드 버스팅|
|:---:|
|<img width="700" alt="image" src="https://github.com/kimchanho97/capstone-frontend/assets/104095041/31614502-86c4-42bb-b3c1-4a310457cad1">|

- **온-프레미스와 클라우드의 결합**: 이 플랫폼은 온-프레미스에 구축된 쿠버네티스 클러스터와 클라우드 환경을 연계하여 안정성과 확장성을 제공합니다. 온-프레미스 환경은 데이터 제어와 보안을, 클라우드 환경은 빠른 리소스 확장을 담당합니다.
- **클라우드 버스팅**: 필요시 GCP의 워커 노드를 자동으로 생성하여 리소스를 동적으로 확장합니다. Prometheus로 모니터링한 CPU 사용량이 임계값을 초과할 경우 Flask 서버를 통해 GCP의 인스턴스 수를 조절하여 확장성을 실현합니다.

<br>

## 6. 플랫폼 소개

### 주요 기능

> - 로그인(GitHub OAuth인증)
> - 프로젝트 생성 &#183; 조회
> - 프로젝트 빌드 &#183; 배포 및 롤백

<br>

### 화면 소개

|**이름**|**이미지**|
|:---:|:---:|
| **메인 페이지** | <img width="500" alt="image" src="https://github.com/kimchanho97/capstone-frontend/assets/104095041/7b9494a2-68b9-401b-81c9-0a32fca9bd36">|
| **프로젝트 페이지** |<img width="500" alt="image" src="https://github.com/kimchanho97/capstone-frontend/assets/104095041/a497f0ec-3ecf-4d30-a6e9-e161a92fb30e">|
| **프로젝트 상세 화면** | <img width="500" alt="image" src="https://github.com/kimchanho97/capstone-frontend/assets/104095041/aa143c61-fb40-4785-8dd3-77b73f2f74af"> |
| **배포 내역 화면** | <img width="500" alt="image" src="https://github.com/kimchanho97/capstone-frontend/assets/104095041/96d36540-020e-4084-9ad2-dac773dd25de"> | 
| **연결 정보 화면** | <img width="500" alt="image" src="https://github.com/kimchanho97/capstone-frontend/assets/104095041/0885572f-f333-44fe-864b-ea948e7b497b"> | 
| **환경 설정 화면** | <img width="500" alt="image" src="https://github.com/kimchanho97/capstone-frontend/assets/104095041/30eea47b-0272-4a70-bb42-767cc21352cf"> | 
| **프로젝트 생성 화면1** | <img width="500" alt="image" src="https://github.com/kimchanho97/capstone-frontend/assets/104095041/a7a3a21f-2ae4-41c6-ae77-da2756931c84"> | 
| **프로젝트 생성 화면2** | <img width="500" alt="image" src="https://github.com/kimchanho97/capstone-frontend/assets/104095041/556b63dc-0386-4546-992a-bb95b4cb5acb"> | 

<br>

## 7. ERD

<img width="700" alt="image" src="https://github.com/kimchanho97/capstone-frontend/assets/104095041/8e3cb2e4-06d2-4794-991b-cdc5703a03e1">
