import os

from django.contrib.auth import login
from django.http import JsonResponse
from django.shortcuts import render
from .serializers import UserSerializer
from rest_framework.decorators import api_view
from .models import Users
from rest_framework.response import Response
import hashlib

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
        return JsonResponse({'success': True, 'data': serialized_user.data})  # 로그인 성공
    else:
        return JsonResponse({'success': False, 'message': '비밀번호가 틀렸습니다.'})  # 비밀번호 오류

@api_view(['POST'])
def get_salt(request):
    user_id = request.data.get('id')
    try:
        user = Users.objects.get(user_id=user_id)
        return JsonResponse({'success': True, 'salt': user.salt})
    except Users.DoesNotExist:
        return JsonResponse({'success': False, 'message': '아이디가 존재하지 않습니다.'})


def pbkdf2(password):
    salt = os.urandom(16)

    hashed_password = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode(),
        salt,
        100000
    )

    return salt, hashed_password
