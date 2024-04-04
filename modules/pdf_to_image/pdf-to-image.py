from typing import List

import dtlpy as dl
import logging
import os
from pathlib import Path
import fitz

logger = logging.getLogger(name=__name__)


class ServiceRunner(dl.BaseServiceRunner):
    """
    This Service contain functions for converting pdf dataloop item to an image dataloop item.
    """

    @staticmethod
    def pdf_item_to_images(item: dl.Item, apply_modality: bool) -> List[dl.Item]:
        """
        Convert pdf dataloop item to an image item.
        :param item: pdf dataloop item.
        :param apply_modality: specify if to use replace modality for visualize the item in the platform.
        :return:
        """

        suffix = Path(item.name).suffix
        if not suffix == '.pdf':
            raise dl.PlatformException(f"Item id : {item.id} is not a PDF file! This functions excepts pdf only")

        # Downloading local path
        local_path = os.path.join(os.getcwd(), 'datasets', item.dataset.id)
        item_local_path = os.path.join(local_path, os.path.dirname(item.filename[1:]))
        item_local_path = item.download(local_path=item_local_path)

        images_paths = ServiceRunner.convert_pdf_to_image(file_path=item_local_path)

        # Uploading all created items - upload bulk
        img_items = item.dataset.items.upload(local_path=images_paths,
                                              item_metadata={
                                                  'user': {'converted_to_image': True, 'original_item_id': item.id}}
                                              )

        if isinstance(img_items, dl.Item):
            img_items = [img_items]
        else:
            img_items = [item for item in img_items]

        if apply_modality:
            # if the pdf contain more than 1 page, only the first image will serve as preview modality.
            first_item = img_items[0]
            ServiceRunner.apply_modality(item=item, ref_item=first_item)

        return img_items

    @staticmethod
    def convert_pdf_to_image(file_path: str) -> List:
        """
        Convert pdf file to a txt file in the platform. Visualize using modality.
        :param file_path: File local path.
        :return: created images paths

        """
        filename = Path(file_path).stem
        # Path to save the generated images
        images_path = os.path.join(os.path.dirname(file_path), 'images_files')
        os.makedirs(images_path, exist_ok=True)
        paths = list()
        # The converted images
        pdf_document = fitz.open(file_path)

        # Iterate over each page
        for page_number in range(pdf_document.page_count):
            # Get the page
            image_filename = os.path.join(images_path, f"{filename}-{page_number}.png")
            page = pdf_document.load_page(page_number)

            # Render the page as an image (PNG)
            image = page.get_pixmap()

            # Save the image to a file
            image.save(image_filename)
            paths.append(images_path)

        # Close the PDF document
        pdf_document.close()

        return paths

    @staticmethod
    def apply_modality(item: dl.Item, ref_item: dl.Item):
        """
        Apply to replace modality in the platform
        :param item: dataloop pdf item
        :param ref_item: dataloop image item
        """
        item.modalities.create(modality_type='replace',
                               name='reference-viewer',
                               mimetype=ref_item.mimetype,
                               ref=ref_item.id)
        item.update(system_metadata=True)


if __name__ == '__main__':
    # dl.setenv('rc')
    # project = dl.projects.get(project_name="text-project")
    # dataset = project.datasets.get(dataset_name="mortgage-dataset")
    # item = dataset.items.get(item_id='65f9984b6861c61ce19447d9')

    dl.setenv('prod')
    project = dl.projects.get(project_name='text-project')
    dataset = project.datasets.get(dataset_name='mortgage-data')
    item = dataset.items.get(item_id='660e92f3aadac655647713e9')

    s = ServiceRunner()
    s.pdf_item_to_images(item=item, apply_modality=True)
