# Deploy Steps (RAG)

## 1. 로컬 이미지 빌드
```bash
cd ~/work/alloc/Alloc-AI
sudo docker build -t alloc-ai-rag:local ./rag
```

## 2. ECR 로그인
```bash
sudo aws ecr get-login-password --region ap-northeast-2 \
| sudo docker login --username AWS --password-stdin 897722680443.dkr.ecr.ap-northeast-2.amazonaws.com
```

## 3. ECR 리포지토리 생성 (없을 때만)
```bash
aws ecr create-repository --repository-name moirai-rag-service --region ap-northeast-2
```

## 4. ECR용 태그 추가
```bash
sudo docker tag alloc-ai-rag:local 897722680443.dkr.ecr.ap-northeast-2.amazonaws.com/moirai-rag-service:latest
```

## 5. ECR 푸시
```bash
sudo docker push 897722680443.dkr.ecr.ap-northeast-2.amazonaws.com/moirai-rag-service:latest
```

## 6. ECS 서비스 이벤트 확인 (배포 실패 원인 확인용)
```bash
aws ecs describe-services \
  --cluster app-ecs-fargate-cluster \
  --services moirai-rag-service \
  --query "services[0].events[0:10]" \
  --output table
```

---

# 주요 이슈와 해결

## 1) `no basic auth credentials`
**원인**  
`docker login`은 일반 사용자로 했는데 `docker push`는 `sudo`로 실행해서 인증 정보가 분리됨.

**해결**
```bash
sudo aws ecr get-login-password --region ap-northeast-2 \
| sudo docker login --username AWS --password-stdin 897722680443.dkr.ecr.ap-northeast-2.amazonaws.com
```

## 2) `repository does not exist`
**원인**  
ECR 리포지토리 자체가 없었음.

**해결**
```bash
aws ecr create-repository --repository-name moirai-rag-service --region ap-northeast-2
```

## 3) GitHub Actions `AWS credentials` 단계 실패  
**에러**  
`The security token included in the request is invalid.`

**원인**  
GitHub Secrets에 잘못된 AWS 키를 넣었거나 만료된 키 사용.

**해결**  
IAM에서 Access Key 재발급 → GitHub Secrets에 재등록
- `AWS_ACCESS_KEY`
- `AWS_SECRET_KEY`

## 4) ECS 배포 실패 (Circuit Breaker)
**에러**  
`image Manifest does not contain descriptor matching platform 'linux/amd64'`

**원인**  
이미지가 `linux/arm64`로 빌드됨. ECS 태스크는 `x86_64`(= amd64).

**해결**  
워크플로 빌드 플랫폼을 `linux/amd64`로 수정  
- `Alloc-AI/.github/workflows/build-rag-service.yml`
- `Alloc-PDF-to-text/.github/workflows/build-pdf-service.yml`
