"""Run the exact Workbench workflow exporter, including its larger source scope."""
from pathlib import Path
import textwrap

import test_campaign_checkout as upstream


class WorkbenchExportTests(upstream.SourceExportTests):
    def setUp(self):
        super().setUp()
        path = Path(__file__).resolve().parents[1] / '.github/workflows/workbench.yml'
        text = path.read_text(encoding='utf-8')
        self.script = textwrap.dedent(text.split('# BEGIN_SOURCE_EXPORT\n', 1)[1].split('# END_SOURCE_EXPORT', 1)[0])
        self.workflow_text = text

    def commit(self, *, link=False):
        content = self.blob('# synthetic source fixture\n')
        source = [('campaign.py', '100644', content), ('workbench.py', '100644', content)]
        if link:
            source.append(('link.py', '120000', self.blob('../../outside')))
        tree = self.tree([
            ('comacbench', '40000', self.tree(source)),
            ('scripts', '40000', self.tree([('dsh_public_boundary.mjs', '100644', content)])),
            ('tests', '40000', self.tree([('test_campaign.py', '100644', content), ('test_workbench.py', '100644', content)])),
            ('data', '40000', self.tree([('strainRateViscosityModel:nu', '100644', content)])),
            ('examples', '40000', self.tree([('workbench', '40000', self.tree([
                ('workload-change-v1.json', '100644', content)]))])),
            ('registry', '40000', self.tree([('product-scope.json', '100644', content)])),
            ('packs', '40000', self.tree([('placeholder.txt', '100644', content)])),
            ('.github', '40000', self.tree([('workflows', '40000', self.tree([
                ('campaign-audit.yml', '100644', self.blob(self.workflow_text))]))]))])
        sha = self.git('commit-tree', tree, '-m', 'synthetic workbench export test')
        self.git('update-ref', 'refs/heads/main', sha)
        return sha

    def test_workbench_material_is_exported_without_research_assets(self):
        proc = self.run_export(self.commit())
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue((self.workspace / 'examples/workbench/workload-change-v1.json').is_file())
        self.assertTrue((self.workspace / 'registry/product-scope.json').is_file())
        self.assertTrue((self.workspace / 'packs/placeholder.txt').is_file())
        self.assertTrue((self.workspace / 'scripts/dsh_public_boundary.mjs').is_file())
        self.assertFalse((self.workspace / 'data').exists())
