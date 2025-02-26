import copy
import json
import os

from loguru import logger

from magic_pdf.data.data_reader_writer import FileBasedDataWriter
from magic_pdf.libs.draw_bbox import draw_layout_bbox, draw_span_bbox
from magic_pdf.pipe.OCRPipe import OCRPipe
from magic_pdf.pipe.TXTPipe import TXTPipe
from magic_pdf.pipe.UNIPipe import UNIPipe

# todo: 设备类型选择 （？）


def json_md_dump(
        pipe,
        md_writer,
        pdf_name,
        content_list,
        md_content,
        orig_model_list,
):
    # 写入模型结果到 model.json

    md_writer.write_string(
        f'{pdf_name}_model.json',
        json.dumps(orig_model_list, ensure_ascii=False, indent=4)
    )

    # 写入中间结果到 middle.json
    md_writer.write_string(
        f'{pdf_name}_middle.json',
        json.dumps(pipe.pdf_mid_data, ensure_ascii=False, indent=4)
    )

    # text文本结果写入到 conent_list.json
    md_writer.write_string(
        f'{pdf_name}_content_list.json',
        json.dumps(content_list, ensure_ascii=False, indent=4)
    )

    # 写入结果到 .md 文件中
    md_writer.write_string(
        f'{pdf_name}.md',
        md_content,
    )


# 可视化
def draw_visualization_bbox(pdf_info, pdf_bytes, local_md_dir, pdf_file_name):
    # 画布局框，附带排序结果
    draw_layout_bbox(pdf_info, pdf_bytes, local_md_dir, pdf_file_name)
    # 画 span 框
    draw_span_bbox(pdf_info, pdf_bytes, local_md_dir, pdf_file_name)


def pdf_parse_main(
        pdf_path: str,
        parse_method: str = 'auto',
        model_json_path: str = None,
        is_json_md_dump: bool = True,
        is_draw_visualization_bbox: bool = True,
        output_dir: str = None
):
    """执行从 pdf 转换到 json、md 的过程，输出 md 和 json 文件到 pdf 文件所在的目录.

    :param pdf_path: .pdf 文件的路径，可以是相对路径，也可以是绝对路径
    :param parse_method: 解析方法， 共 auto、ocr、txt 三种，默认 auto，如果效果不好，可以尝试 ocr
    :param model_json_path: 已经存在的模型数据文件，如果为空则使用内置模型，pdf 和 model_json 务必对应
    :param is_json_md_dump: 是否将解析后的数据写入到 .json 和 .md 文件中，默认 True，会将不同阶段的数据写入到不同的 .json 文件中（共3个.json文件），md内容会保存到 .md 文件中
    :param is_draw_visualization_bbox: 是否绘制可视化边界框，默认 True，会生成布局框和 span 框的图像
    :param output_dir: 输出结果的目录地址，会生成一个以 pdf 文件名命名的文件夹并保存所有结果
    """
    try:
        pdf_name = os.path.basename(pdf_path).split('.')[0]
        pdf_path_parent = os.path.dirname(pdf_path)

        if output_dir:
            output_path = os.path.join(output_dir, pdf_name)
        else:
            output_path = os.path.join(pdf_path_parent, pdf_name)

        output_image_path = os.path.join(output_path, 'images')

        # 获取图片的父路径，为的是以相对路径保存到 .md 和 conent_list.json 文件中
        image_path_parent = os.path.basename(output_image_path)

        pdf_bytes = open(pdf_path, 'rb').read()  # 读取 pdf 文件的二进制数据

        orig_model_list = []

        if model_json_path:
            # 读取已经被模型解析后的pdf文件的 json 原始数据，list 类型
            model_json = json.loads(open(model_json_path, 'r', encoding='utf-8').read())
            orig_model_list = copy.deepcopy(model_json)
        else:
            model_json = []

        # 执行解析步骤
        image_writer, md_writer = FileBasedDataWriter(output_image_path), FileBasedDataWriter(output_path)

        # 选择解析方式
        if parse_method == 'auto':
            jso_useful_key = {'_pdf_type': '', 'model_list': model_json}
            pipe = UNIPipe(pdf_bytes, jso_useful_key, image_writer)
        elif parse_method == 'txt':
            pipe = TXTPipe(pdf_bytes, model_json, image_writer)
        elif parse_method == 'ocr':
            pipe = OCRPipe(pdf_bytes, model_json, image_writer)
        else:
            logger.error('unknown parse method, only auto, ocr, txt allowed')
            exit(1)

        # 执行分类
        pipe.pipe_classify()

        # 如果没有传入模型数据，则使用内置模型解析
        if len(model_json) == 0:
            pipe.pipe_analyze()  # 解析
            orig_model_list = copy.deepcopy(pipe.model_list)

        # 执行解析
        pipe.pipe_parse()

        # 保存 text 和 md 格式的结果
        content_list = pipe.pipe_mk_uni_format(image_path_parent, drop_mode='none')
        md_content = pipe.pipe_mk_markdown(image_path_parent, drop_mode='none')

        if is_json_md_dump:
            json_md_dump(pipe, md_writer, pdf_name, content_list, md_content, orig_model_list)

        if is_draw_visualization_bbox:
            draw_visualization_bbox(pipe.pdf_mid_data['pdf_info'], pdf_bytes, output_path, pdf_name)

    except Exception as e:
        logger.exception(e)


# 测试
if __name__ == '__main__':
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    demo_names = ['demo']
    for name in demo_names:
        file_path = os.path.join(current_script_dir, f'{name}.pdf')
        pdf_parse_main(file_path)