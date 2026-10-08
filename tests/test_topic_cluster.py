import unittest

from scripts.build_posts import build_cluster_navigation, build_toc_and_content


class TopicClusterTests(unittest.TestCase):
    def test_unassigned_article_does_not_gain_cluster_navigation(self):
        self.assertEqual(build_cluster_navigation({'slug': 'other'}, []), '')

    def test_navigation_excludes_current_page_and_prioritizes_hub(self):
        current = {'slug': 'speed', 'title': 'Speed', 'cluster_id': 'walking-pad-desk'}
        posts = [current,
                 {'slug': 'setup', 'title': 'A setup', 'cluster_id': 'walking-pad-desk'},
                 {'slug': 'hub', 'title': 'The guide', 'cluster_id': 'walking-pad-desk', 'cluster_role': 'hub'},
                 {'slug': 'unrelated', 'title': 'Other', 'cluster_id': 'another'}]
        navigation = build_cluster_navigation(current, posts)
        self.assertNotIn('/blogs/speed/', navigation)
        self.assertNotIn('/blogs/unrelated/', navigation)
        self.assertLess(navigation.index('/blogs/hub/'), navigation.index('/blogs/setup/'))
        toc, content = build_toc_and_content(navigation)
        self.assertIn('explore-the-walking-pad-desk-guide', toc)
        self.assertIn('/blogs/setup/', content)


if __name__ == '__main__':
    unittest.main()
