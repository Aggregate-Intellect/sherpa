from sherpa_ai.output_parsers import LinkParser


def test_link_parser():
    resource_text = """
        resource1, Link:https://link1.com
        resource2, Link:https://link2.com
        resource3, Link:https://link3.com
    """

    output_text = "sentence1 [1], sentence2 [2], sentence3 [3]"

    link_parser = LinkParser()
    modified_resource_text = link_parser.parse_output(resource_text, True)
    assert (
        modified_resource_text
        == """
        resource1, DocID:[1]
        resource2, DocID:[2]
        resource3, DocID:[3]
    """
    )

    modified_output_text = link_parser.parse_output(output_text, False)

    assert (
        modified_output_text
        == "sentence1 <https://link1.com|[1]>, sentence2 <https://link2.com|[2]>, sentence3 <https://link3.com|[3]>"  # noqa: E501
    )
