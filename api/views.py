import os

from django.contrib.auth import login, logout
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.middleware.csrf import get_token

from .serializers import UserSerializer
from rest_framework.decorators import api_view
from .models import Users, Info, AccessHistory
from rest_framework.response import Response
from .code import HistoryCode, HttpStatusCode
import hashlib
from .util import color

@api_view(['POST'])
def get_salt(request):
    user_id = request.data.get('id')
    try:
        user = Users.objects.get(user_id=user_id)
        return JsonResponse({'success': True, 'salt': user.salt}, status=HttpStatusCode.ok)
    except Users.DoesNotExist:
        return JsonResponse({'success': False, 'message': '아이디가 존재하지 않습니다.'}, status=HttpStatusCode.bad_request)

@api_view(['POST'])
def do_login(request):
    print(color(f'login -> request.COOKIES: [yellow]{request.COOKIES}[/yellow]'))
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
        create_history(request, user_id, HistoryCode.fail)
        return JsonResponse({'success': False, 'message': '오류가 발생했습니다.'}, status=HttpStatusCode.bad_request)

    # DB에 저장된 비밀번호와 입력된 비밀번호를 비교
    if user_pw == user.password:  # 비밀번호 비교
        login(request, user)
        # print(request.session.session_key)
        create_history(request, user_id, HistoryCode.success)
        data = serialized_user.data | {'session_id': request.session.session_key} | {'csrftoken': get_token(request)}
        print(color(f'[red][LOGIN][/red] userId: [red]{user_id}[/red]'))
        return JsonResponse({'success': True, 'data': data}, status=HttpStatusCode.ok)  # 로그인 성공
    else:
        create_history(request, user_id, HistoryCode.fail)
        return JsonResponse({'success': False, 'message': '계정이 존재하지않습니다.'}, status=HttpStatusCode.bad_request)  # 비밀번호 오류

@api_view(['POST'])
def check_login(request):
    print(color(f'check_login -> request.COOKIES: [yellow]{request.COOKIES}[/yellow]'))
    if request.user.is_authenticated:
        return JsonResponse({'success': True}, status=HttpStatusCode.ok)
    return JsonResponse({'success': False, 'message': '로그인 된 상태가 아닙니다.'}, status=HttpStatusCode.bad_request)

@api_view(['POST'])
def do_logout(request):
    print(color(f'logout -> request.COOKIES: [yellow]{request.COOKIES}[/yellow]'))
    if request.user.is_authenticated:
        print(color(f'[red][LOGOUT][/red] userId: [red]{request.user.user_id}[/red]'))
        logout(request)
    return JsonResponse({'success': True, 'data': {'csrftoken': get_token(request)}}, status=HttpStatusCode.ok)



@api_view(['POST'])
def do_register(request):
    if request.method == 'POST':
        user_id = request.data.get('id')
        user_pw = request.data.get('pw')
        user_email = request.data.get('email')
        user_nickname = request.data.get('nickname')
        user_salt = request.data.get('salt')

        # 유효성 검사
        if not user_id or not user_pw:
            return JsonResponse({'success': False, 'message': '모든 필드를 입력해야 합니다.'}, status=HttpStatusCode.bad_request)

        # ID 중복 확인
        if Users.objects.filter(user_id=user_id).exists():
            return JsonResponse({'success': False, 'message': '이미 사용 중인 아이디입니다.'}, status=HttpStatusCode.bad_request)

        # Email 중복 확인(None이면 패스)
        if user_email and Users.objects.filter(email=user_email).exists():
            return JsonResponse({'success': False, 'message': '이미 사용 중인 이메일입니다.'}, status=HttpStatusCode.bad_request)

        if not user_salt:
            return JsonResponse({'success': False, 'message': '값이 누락되었습니다.'}, status=HttpStatusCode.bad_request)

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
                    region='서울시',
                    diseases='없음',
                )
                new_info.save()

            create_history(request, user_id, HistoryCode.registration)
            print(color(f'[red][REGISTER][/red] userId: [red]{user_id}[/red]'))

            return JsonResponse({'success': True, 'message': '회원가입이 완료되었습니다.'}, status=HttpStatusCode.created)
        except Exception as e:
            return JsonResponse({'success': False, 'message': '회원가입 중 오류가 발생했습니다.'}, status=HttpStatusCode.bad_request)

    return JsonResponse({'success': False, 'message': '잘못된 요청입니다.'}, status=HttpStatusCode.bad_request)

@api_view(['POST'])
def update_user_info(request):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': '잘못된 요청입니다.'}, status=HttpStatusCode.forbidden)
    if request.method == 'POST':
        try:
            # 현재 로그인한 사용자 가져오기
            user = request.user

            # Users 테이블에서 해당 사용자 객체 가져오기
            user_record = get_object_or_404(Users, user_id=user.user_id)

            # Info 테이블에서 해당 사용자 정보 가져오기
            info_record = get_object_or_404(Info, id=user_record.id)

            # POST 데이터 가져오기
            user_email = request.data.get('email')
            user_region = request.data.get('region')
            user_disease = request.data.get('diseases')

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
            # print(f"User: {user_record.user_id}, Email: {user_record.email}")
            # print(f"Info: ID {info_record.id}, Region: {info_record.region}, Disease: {info_record.diseases}")

            create_history(request, user.user_id, HistoryCode.update_info)

            print(color(f'[red][UPDATE-INFO][/red] userId: [red]{user_record.user_id}[/red]'))

            return JsonResponse({'success': True}, status=HttpStatusCode.ok)

        except Exception as e:
            # 예외 처리
            return JsonResponse({'success': False, 'message': '알 수 없는 오류가 발생하였습니다.'}, status=HttpStatusCode.internal_server_error)
    else:
        return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=HttpStatusCode.method_not_allowed)

@api_view(['POST'])
def update_password(request):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': '잘못된 요청입니다.'}, status=HttpStatusCode.forbidden)
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
            return JsonResponse({'success': False, 'message': '현재 비밀번호가 일치하지않습니다.'}, status=HttpStatusCode.not_found)

        user_record.save()
        create_history(request, user.user_id, HistoryCode.update_password)
        data = {
            'session_id': request.session.session_key,
            'csrftoken': get_token(request),
        }
        print(color(f'[red][UPDATE-PASS][/red] userId: [red]{user_record.user_id}[/red]'))
        return JsonResponse({'success': True, 'data': data}, status=HttpStatusCode.ok)

    except Exception as e:
        return JsonResponse({'success': False, 'message': '예상치 못한 오류가 발생하였습니다.'}, status=HttpStatusCode.internal_server_error)

@api_view(['POST'])
def get_user_data(request):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': '잘못된 요청입니다.'}, status=HttpStatusCode.forbidden)
    if request.method == 'POST':
        try:
            # 현재 로그인한 사용자 가져오기
            user = request.user

            # Users 테이블에서 해당 사용자 객체 가져오기
            user_record = get_object_or_404(Users, user_id=user.user_id)

            # Info 테이블에서 해당 사용자 정보 가져오기
            info_record = get_object_or_404(Info, id=user_record.id)

            response_json = {
                'user_id': user_record.user_id,
                'email': user_record.email,
                'region': info_record.region,
                'diseases': info_record.diseases,
            }

            # 디버그 출력 (필요시)
            # print(f"User: {user_record.user_id}, Email: {user_record.email}")
            # print(f"Info: ID {info_record.id}, Region: {info_record.region}, Disease: {info_record.diseases}")

            return JsonResponse({'success': True, 'data': response_json}, status=HttpStatusCode.ok)

        except Exception as e:
            print(color(f'[red]{e}[/red]'))
            # 예외 처리
            return JsonResponse({'success': False, 'message': '알 수 없는 오류가 발생하였습니다.'}, status=HttpStatusCode.internal_server_error)
    else:
        return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=HttpStatusCode.method_not_allowed)

@api_view(['POST'])
def get_access_history(request):
    if request.user.is_authenticated:
        # user_id에 맞는 모든 AccessHistory 레코드를 가져옵니다.
        access_history = AccessHistory.objects.filter(user_id=request.user.user_id)

        # 결과를 data 객체에 담기
        data = []
        for record in access_history:
            data.append({
                'access_time': record.access_time,
                'access_ip': record.access_ip,
                'result': record.result,
            })

        return JsonResponse({'success': True, 'data': data}, status=200)
    else:
        return JsonResponse({'success': False, 'message': '올바른 접근이 아닙니다.'}, status=400)

def pbkdf2(password):
    salt = os.urandom(16)

    hashed_password = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode(),
        salt,
        100000
    )

    return salt, hashed_password

def get_current_time():
    from django.utils import timezone
    return timezone.now()

def create_history(request, user_id, code):
    with transaction.atomic():
        new_access_history = AccessHistory(
            user_id=user_id,
            access_time=get_current_time(),
            access_ip=get_ip_addr(request),
            result=code,
        )

        new_access_history.save()
    return None

def get_ip_addr(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # 'X-Forwarded-For' 헤더는 여러 개의 IP가 쉼표로 구분될 수 있으므로 첫 번째 IP를 사용합니다.
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


