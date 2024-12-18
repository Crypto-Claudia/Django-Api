import os

from django.contrib.auth import login
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from .serializers import UserSerializer
from rest_framework.decorators import api_view
from .models import Users, Info
from rest_framework.response import Response
import hashlib

@csrf_exempt
@api_view(['POST'])
def get_salt(request):
    user_id = request.data.get('id')
    try:
        user = Users.objects.get(user_id=user_id)
        return JsonResponse({'success': True, 'salt': user.salt})
    except Users.DoesNotExist:
        return JsonResponse({'success': False, 'message': '아이디가 존재하지 않습니다.'})

@api_view(['POST'])
def do_login(request):
    # user_id = request.GET.get('id')
    user_id = request.data.get('id')
    # user_pw = request.GET.get('pw')
    user_pw = request.data.get('pw')
    # 테스트용 SHA256코드

    # 사용자가 입력한 ID에 해당하는 사용자 정보를 DB에서 조회
    try:
        user = Users.objects.get(user_id=user_id)  # Users 모델에서 ID로 검색
        serialized_user = UserSerializer(instance=user)
    except Users.DoesNotExist:
        # 해당 ID를 가진 사용자가 없다면 로그인 실패 처리
        return JsonResponse({'success': False, 'message': '아이디가 존재하지 않습니다.'})

    # DB에 저장된 비밀번호와 입력된 비밀번호를 비교
    if user_pw == user.password:  # 비밀번호 비교
        login(request, user)
        # print(request.session.session_key)
        from django.middleware.csrf import get_token
        data = serialized_user.data | {'session_id': request.session.session_key} | {'csrftoken': get_token(request)}
        return JsonResponse({'success': True, 'data': data})  # 로그인 성공
    else:
        return JsonResponse({'success': False, 'message': '비밀번호가 틀렸습니다.'})  # 비밀번호 오류


@api_view(['POST'])
def do_register(request):
    if request.method == 'POST':
        user_id = request.POST.get('id')
        user_pw = request.POST.get('pw')
        user_email = request.POST.get('email')
        user_nickname = request.POST.get('nickname')
        user_salt = request.POST.get('salt')

        print(f'salt: {user_salt}')

        # 유효성 검사
        if not user_id or not user_pw:
            return JsonResponse({'success': False, 'message': '모든 필드를 입력해야 합니다.'})

        # ID 중복 확인
        if Users.objects.filter(user_id=user_id).exists():
            return JsonResponse({'success': False, 'message': '이미 사용 중인 아이디입니다.'})

        # Email 중복 확인(None이면 패스)
        if user_email and Users.objects.filter(email=user_email).exists():
            return JsonResponse({'success': False, 'message': '이미 사용 중인 이메일입니다.'})

        if not user_salt:
            return JsonResponse({'success': False, 'message': '값이 누락되었습니다.'})

        # 닉네임이 없으면 id로 교체
        if not user_nickname:
            user_nickname = user_id

        # 새로운 사용자 생성 및 저장
        try:
            with transaction.atomic():
                # 새로운 사용자 생성
                new_user = Users(
                    user_id=user_id,
                    password=user_pw,  # 해싱된 비밀번호 저장
                    email=user_email,
                    nickname=user_nickname,
                    salt=user_salt
                )
                new_user.save()

                # Info 생성
                new_info = Info(
                    id=new_user,  # ForeignKey에 Users 인스턴스 할당
                    region=None,
                    diseases=None,
                )
                new_info.save()

            return JsonResponse({'success': True, 'message': '회원가입이 완료되었습니다.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': '회원가입 중 오류가 발생했습니다.', 'error': str(e)})

    return JsonResponse({'success': False, 'message': '잘못된 요청입니다.'}, status=400)

@api_view(['POST'])
def update_user_info(request):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': '잘못된 요청입니다.'})
    if request.method == 'POST':
        try:
            # 현재 로그인한 사용자 가져오기
            user = request.user

            # Users 테이블에서 해당 사용자 객체 가져오기
            user_record = get_object_or_404(Users, user_id=user.user_id)

            # Info 테이블에서 해당 사용자 정보 가져오기
            info_record = get_object_or_404(Info, id=user_record.id)

            # POST 데이터 가져오기
            user_email = request.POST.get('email')
            user_region = request.POST.get('region')
            user_disease = request.POST.get('disease')

            # Users 테이블 업데이트
            if user_email:
                user_record.email = user_email

            # Info 테이블 업데이트
            if user_region:
                info_record.region = user_region
            if user_disease:
                info_record.diseases = user_disease

            # 데이터 저장
            user_record.save()
            info_record.save()

            # 디버그 출력 (필요시)
            print(f"User: {user_record.user_id}, Email: {user_record.email}")
            print(f"Info: ID {info_record.id}, Region: {info_record.region}, Disease: {info_record.diseases}")

            return JsonResponse({'success': True}, status=200)

        except Exception as e:
            # 예외 처리
            return JsonResponse({'success': False, 'message': '알 수 없는 오류가 발생하였습니다.'}, status=500)
    else:
        return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=400)

@api_view(['POST'])
def update_password(request):
    if not request.user.is_authenticated:
        print('비밀번호 변경 프로세스')
        return JsonResponse({'success': False, 'message': '잘못된 요청입니다.'})
    try:
        user = request.user
        user_record = get_object_or_404(Users, user_id=user.user_id)
        # 데이터 가져오기
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        new_salt = request.data.get('new_salt')

        if user_record.password == current_password:
            user_record.password = new_password
            user_record.salt = new_salt
        else:
            return JsonResponse({'success': False, 'message': '현재 비밀번호가 일치하지않습니다.'})

        user_record.save()
        return JsonResponse({'success': True})

    except Exception as e:
        return JsonResponse({'success': False, 'message': '예상치 못한 오류가 발생하였습니다.'})


def pbkdf2(password):
    salt = os.urandom(16)

    hashed_password = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode(),
        salt,
        100000
    )

    return salt, hashed_password
