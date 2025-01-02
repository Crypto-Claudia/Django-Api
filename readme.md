# **테스트 방법**

## 데이터 베이스 복원하기

[db_init.bat](db_init.bat)을 열고 `PASSWORD`를 수정 후 실행하거나 아래 구문을 커맨드라인에 복붙

`mysql -u root -pPASSWORD > init.sql`

`PASSWORD` 는 DB의 루트 패스워드로 교체

## 서버 작동 시키기

루트 디렉토리에서 `python manage.py runserver`

## 덤프 파일 내 테스트 계정

`id`: test6666

`pw`: test6666