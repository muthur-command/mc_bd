"""镜像管理API"""
import io
from typing import Annotated
from urllib.parse import unquote

from fastapi import APIRouter, File, Path, Query, UploadFile
from fastapi.responses import StreamingResponse

from backend.common.log import log
from backend.common.response.response_code import CustomResponse
from backend.common.response.response_schema import ResponseModel, ResponseSchemaModel, response_base
from backend.common.security.jwt import DependsJwtAuth
from backend.plugin.docker.schema.docker import (
    BuildImageParam,
    ImageDetailResponse,
    ImageListResponse,
    PullImageParam,
)
from backend.plugin.docker.service.docker_service import docker_service

router = APIRouter()


@router.get('', summary='获取镜像列表', dependencies=[DependsJwtAuth])
async def list_images(
    all: Annotated[bool, Query(description='是否包含中间镜像')] = False,
) -> ResponseSchemaModel[list[ImageListResponse]]:
    """获取镜像列表"""
    images = docker_service.list_images(all=all)
    return response_base.success(data=images)


@router.post('/pull', summary='拉取镜像', dependencies=[DependsJwtAuth])
async def pull_image(obj: PullImageParam) -> ResponseModel:
    """拉取镜像"""
    try:
        image = docker_service.pull_image(obj.image, obj.tag)
        return response_base.success(data=image)
    except Exception as e:
        log.error(f'拉取镜像失败: {e}', exc_info=True)
        # 提取错误信息
        error_msg = str(e) if e else '拉取镜像失败'
        
        # 如果错误信息包含 Docker 命令执行的详细信息，尝试提取关键部分
        if 'The command executed was' in error_msg:
            # 尝试从错误信息中提取有用的部分
            # 通常错误信息格式类似：
            # "The command executed was `/usr/bin/docker image pull busybox:latest`. 
            #  It returned with code 1. The content of stdout/stderr can be found above..."
            lines = error_msg.split('\n')
            useful_lines = []
            for line in lines:
                line = line.strip()
                # 跳过命令执行信息和空行
                if line and 'The command executed was' not in line and 'returned with code' not in line:
                    # 跳过关于 stdout/stderr 的说明
                    if 'stdout' not in line.lower() and 'stderr' not in line.lower() and 'stacktrace' not in line.lower():
                        useful_lines.append(line)
            
            if useful_lines:
                # 使用第一个有用的错误行
                error_msg = useful_lines[0]
            else:
                # 如果没有找到有用的行，使用简化的错误信息
                error_msg = f'Docker 命令执行失败 (镜像: {obj.image}:{obj.tag})'
        
        return response_base.fail(res=CustomResponse(code=400, msg=f'拉取镜像失败: {error_msg}'))


@router.delete('/{image_id}', summary='删除镜像', dependencies=[DependsJwtAuth])
async def remove_image(
    image_id: Annotated[str, Path(description='镜像ID或名称')],
    force: Annotated[bool, Query(description='是否强制删除')] = False,
) -> ResponseModel:
    """删除镜像"""
    # FastAPI 会自动解码 URL 编码的路径参数，但为了确保，我们显式解码
    decoded_image_id = unquote(image_id)
    log.info(f'删除镜像: {decoded_image_id}, force={force}')
    docker_service.remove_image(decoded_image_id, force=force)
    return response_base.success()


@router.post('/build', summary='构建镜像', dependencies=[DependsJwtAuth])
async def build_image(obj: BuildImageParam) -> ResponseModel:
    """构建镜像（使用服务器路径）"""
    try:
        image = docker_service.build_image(
            path=obj.path,
            tag=obj.tag,
            dockerfile=obj.dockerfile,
            build_args=obj.build_args,
        )
        return response_base.success(data=image)
    except DockerException as e:
        error_message = str(e)
        # 提取更友好的错误信息
        if "command executed was" in error_message:
            error_message = error_message.split("The command executed was")[0].strip()
            error_message = error_message.split("The content of stdout can be found")[0].strip()
            error_message = error_message.split("The content of stderr can be found")[0].strip()
        log.error(f'构建镜像失败: {error_message}')
        return response_base.fail(res=CustomResponse(code=400, msg=f'构建镜像失败: {error_message}'))
    except Exception as e:
        log.error(f'构建镜像时发生未知错误: {e}', exc_info=True)
        return response_base.fail(res=CustomResponse(code=500, msg=f'构建镜像时发生未知错误: {str(e)}'))


@router.post('/build/upload', summary='上传文件构建镜像', dependencies=[DependsJwtAuth])
async def build_image_from_upload(
    file: Annotated[UploadFile, File(description='构建上下文 tar 文件')],
    tag: Annotated[str, Query(description='镜像标签')],
    dockerfile: Annotated[str, Query(description='Dockerfile路径')] = 'Dockerfile',
) -> ResponseModel:
    """从上传的 tar 文件构建镜像"""
    try:
        # 读取上传的文件内容
        tar_data = await file.read()
        
        if not tar_data:
            return response_base.fail(res=CustomResponse(code=400, msg='上传的文件为空'))
        
        # 验证文件类型（简单检查文件头）
        if not tar_data.startswith(b'PK') and not tar_data.startswith(b'\x1f\x8b') and not tar_data.startswith(b'ustar'):
            # tar 文件可能以不同的格式开始，这里只做基本检查
            # 实际验证会在解压时进行
            pass
        
        # 构建镜像
        import asyncio
        from functools import partial
        
        loop = asyncio.get_event_loop()
        image = await loop.run_in_executor(
            None,
            partial(docker_service.build_image_from_tar, tar_data, tag, dockerfile),
        )
        
        return response_base.success(data=image)
    except DockerException as e:
        error_message = str(e)
        # 提取更友好的错误信息
        if "command executed was" in error_message:
            error_message = error_message.split("The command executed was")[0].strip()
            error_message = error_message.split("The content of stdout can be found")[0].strip()
            error_message = error_message.split("The content of stderr can be found")[0].strip()
        log.error(f'构建镜像失败: {error_message}')
        return response_base.fail(res=CustomResponse(code=400, msg=f'构建镜像失败: {error_message}'))
    except Exception as e:
        log.error(f'构建镜像时发生未知错误: {e}', exc_info=True)
        error_msg = str(e) if e else '构建镜像失败'
        return response_base.fail(res=CustomResponse(code=400, msg=f'构建镜像失败: {error_msg}'))


@router.get('/{image_id}/export', summary='导出镜像', dependencies=[DependsJwtAuth])
async def export_image(
    image_id: Annotated[str, Path(description='镜像ID或名称')],
) -> StreamingResponse:
    """导出镜像为 tar 文件"""
    import asyncio
    from functools import partial
    
    # 使用异步方式执行 docker save 命令，避免阻塞
    loop = asyncio.get_event_loop()
    tar_data = await loop.run_in_executor(
        None,
        partial(docker_service.save_image, image_id),
    )
    
    # 生成文件名（使用镜像ID的前12位）
    filename = f'{image_id[:12] if len(image_id) > 12 else image_id}.tar'
    
    return StreamingResponse(
        io.BytesIO(tar_data),
        media_type='application/x-tar',
        headers={
            'Content-Disposition': f'attachment; filename={filename}',
            'Content-Length': str(len(tar_data)),
        },
    )


@router.post('/import', summary='导入镜像', dependencies=[DependsJwtAuth])
async def import_image(file: Annotated[UploadFile, File(description='镜像 tar 文件')]) -> ResponseModel:
    """从 tar 文件导入镜像"""
    try:
        # 读取上传的文件内容
        tar_data = await file.read()
        
        if not tar_data:
            return response_base.fail(res=CustomResponse(code=400, msg='上传的文件为空'))
        
        # 验证文件类型（简单检查文件头）
        if not tar_data.startswith(b'PK') and not tar_data.startswith(b'\x1f\x8b'):
            # tar 文件可能以不同的格式开始，这里只做基本检查
            # 实际验证会在 docker load 时进行
            pass
        
        # 导入镜像
        import asyncio
        from functools import partial
        
        loop = asyncio.get_event_loop()
        image = await loop.run_in_executor(
            None,
            partial(docker_service.load_image, tar_data),
        )
        
        return response_base.success(data=image)
    except Exception as e:
        log.error(f'导入镜像失败: {e}', exc_info=True)
        error_msg = str(e) if e else '导入镜像失败'
        return response_base.fail(res=CustomResponse(code=400, msg=f'导入镜像失败: {error_msg}'))


@router.get('/{image_id}/detail', summary='获取镜像详情', dependencies=[DependsJwtAuth])
async def get_image_detail(
    image_id: Annotated[str, Path(description='镜像ID或名称')],
) -> ResponseSchemaModel[ImageDetailResponse]:
    """获取镜像详情，包括 Dockerfile details 和 layers"""
    import asyncio
    from functools import partial
    
    # 解码 URL 编码的路径参数
    decoded_image_id = unquote(image_id)
    
    # 使用异步方式执行，避免阻塞
    loop = asyncio.get_event_loop()
    detail = await loop.run_in_executor(
        None,
        partial(docker_service.get_image_detail, decoded_image_id),
    )
    
    return response_base.success(data=detail)

