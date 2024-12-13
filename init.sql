-- USERS 테이블 생성
CREATE TABLE USERS (
    ID VARCHAR(16) NOT NULL PRIMARY KEY,
    PASSWORD VARCHAR(64) NOT NULL, -- SHA256은 64자의 고정 길이 해시
    EMAIL VARCHAR(40),
    NICKNAME VARCHAR(20) NOT NULL,
    REGISTER TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- 현재 시간을 기본값으로 설정
    LAST_LOGIN VARCHAR(255)  -- 새로운 필드 추가
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- INFO 테이블 생성
CREATE TABLE INFO (
    ID VARCHAR(16) NOT NULL,
    REGION VARCHAR(16),
    DISEASES VARCHAR(100),
    PRIMARY KEY (ID),
    FOREIGN KEY (ID) REFERENCES USERS(ID) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

INSERT INTO USERS (ID, PASSWORD, EMAIL, NICKNAME, REGISTER)
VALUES ('testid', '9f735e0df9a1ddc702bf0a1a7b83033f9f7153a00c29de82cedadc9957289b05', 'email@test.com', '테스트계정', '2024-12-08 10:30:00');
-- password: testpassword
INSERT INTO INFO VALUES ('testid', '울산', '축농증, 비만');

INSERT INTO USERS (ID, PASSWORD, EMAIL, NICKNAME) VALUES ('admin', '749f09bade8aca755660eeb17792da880218d4fbdc4e25fbec279d7fe9f65d70', 'admin@test.com', '관리자계정');
-- password: adminpassword
INSERT INTO INFO VALUES ('admin', '부산', '기관지염');



-- 아래는 테이블 삭제
drop table auth_group_permissions;
drop table auth_user_user_permissions;
drop table auth_permission;
drop table auth_user_groups;
drop table auth_group;
drop table django_admin_log;
drop table django_content_type;
drop table django_migrations;
drop table django_session;
drop table auth_user;

DROP TABLE INFO;
DROP TABLE USERS;

-- 일괄 마이그레이션하면 오류남,, app먼저 진행후 api 마이그레이션 구구혓