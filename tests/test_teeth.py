"""牙齿测试 — 每个机制的"强制"必须真的咬人。

这个项目的全部价值在于机制**有牙齿** (机器强制), 而不是散文 (会被无视)。
所以测试只测一件事: **各道门在该拒绝时真的拒绝, 在该放行时真的放行。**

零依赖 (stdlib unittest) — 契合项目极简性格。跑法:
    python3 -m unittest discover tests -v
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import contract        # noqa: E402
import fitness_bridge  # noqa: E402
import ledger          # noqa: E402


class LedgerGates(unittest.TestCase):
    """不对称门 / 证伪门 / WIP 上限 — 全部代码层强制, 不是叮嘱。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self._orig = ledger.LEDGER
        ledger.LEDGER = Path(self.tmp.name) / "ideas.jsonl"

    def tearDown(self):
        ledger.LEDGER = self._orig
        self.tmp.cleanup()

    def _add(self, hyp="h", asym="别人做不了因为X", falsify="若Y则死", lens="asymmetry"):
        ns = type("A", (), {"hypothesis": hyp, "asymmetry": asym, "falsify": falsify,
                            "lens": lens, "bet": "medium"})()
        ledger.add(ns)

    def test_asymmetry_gate_rejects_empty(self):
        """不答'别人为什么做不了' → 拒收 (红海门)。"""
        with self.assertRaises(SystemExit):
            self._add(asym="")
        with self.assertRaises(SystemExit):
            self._add(asym="   ")

    def test_falsify_gate_rejects_empty(self):
        """不事前写死证伪判据 → 拒收 (防事后自我美化)。"""
        with self.assertRaises(SystemExit):
            self._add(falsify="")

    def test_wip_limit_forces_killing(self):
        """WIP 满 → 拒收新想法 (先杀再提; 防想法灌水)。"""
        for i in range(ledger.WIP_LIMIT):
            self._add(hyp=f"想法{i}")
        with self.assertRaises(SystemExit):
            self._add(hyp="第七个")
        # 杀一个 → 又能提了
        ns = type("A", (), {"id": 1, "status": "killed", "outcome": "死因"})()
        ledger.setst(ns)
        self._add(hyp="现在可以了")   # 不抛 = 通过

    def test_valid_idea_accepted_with_provenance(self):
        """合规想法收下, 且记录来源透镜 (元学习的原料)。"""
        self._add(lens="contradiction")
        rows = json.loads(ledger.LEDGER.read_text().splitlines()[0])
        self.assertEqual(rows["lens"], "contradiction")
        self.assertEqual(rows["status"], "proposed")


class ContractTeeth(unittest.TestCase):
    """输出契约 — think 说'无事可做'=失败; build 必须写赛道且可归因; watch 唯一豁免。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        tp = Path(self.tmp.name)
        self._orig = (contract.LEDGER, contract.JOURNAL)
        contract.LEDGER = tp / "ideas.jsonl"
        contract.JOURNAL = tp / "journal.md"
        contract.LEDGER.write_text('{"id":1}\n')
        contract.JOURNAL.write_text("j\n")

    def tearDown(self):
        contract.LEDGER, contract.JOURNAL = self._orig
        self.tmp.cleanup()

    def test_think_fails_when_ledger_unchanged(self):
        before = contract.snapshot()
        ok, msg = contract.verify("think", before)
        self.assertFalse(ok)
        self.assertIn("无事可做", msg)

    def test_think_passes_when_ledger_changed(self):
        before = contract.snapshot()
        contract.LEDGER.write_text('{"id":1}\n{"id":2}\n')
        ok, _ = contract.verify("think", before)
        self.assertTrue(ok)

    def test_watch_is_the_only_shift_allowed_to_do_nothing(self):
        before = contract.snapshot()
        ok, _ = contract.verify("watch", before)
        self.assertTrue(ok)

    def test_build_fails_without_attributable_track_commit(self):
        """伤疤 #8: build 检**赛道上带 trailer 的 commit 数**, 车库 commit 不算, 别人的 commit 不算。"""
        before = contract.snapshot()
        contract.LEDGER.write_text('{"id":1}\n{"id":2}\n')   # 先缴思考税, 隔离赛道契约
        ok, msg = contract.verify("build", before)
        self.assertFalse(ok)
        self.assertIn("可归因", msg)

    def test_reflect_fails_on_silent_journal(self):
        before = contract.snapshot()
        contract.LEDGER.write_text('{"id":1}\n{"id":2}\n')   # 先缴思考税, 隔离 journal 契约
        ok, msg = contract.verify("reflect", before)
        self.assertFalse(ok)
        self.assertIn("journal", msg)


class ThinkingTax(unittest.TestCase):
    """**思考不是一个班次, 是每一次动作的税。** (用户 2026-07-12)

    验尸案由: 把 think 做成独立的、排期的班次, **在结构上等于宣布"其他所有班次都可以不思考"**。
    而"排期的思考"就是打工人的定义 —— 想法成了任务, 不是本能。
    (亲证: 我先给思考排了个 25 分钟后的班, 然后**等用户叫我**才想。)
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        tp = Path(self.tmp.name)
        self._orig = (contract.LEDGER, contract.JOURNAL)
        contract.LEDGER = tp / "ideas.jsonl"
        contract.JOURNAL = tp / "journal.md"
        contract.LEDGER.write_text('{"id":1}\n')
        contract.JOURNAL.write_text("j\n")

    def tearDown(self):
        contract.LEDGER, contract.JOURNAL = self._orig
        self.tmp.cleanup()

    def test_every_shift_but_watch_pays_the_tax(self):
        """干完活却什么都没学到 = FAILED_SHIFT。**每一个**班, 不只是 think。"""
        before = contract.snapshot()
        for shift in ("build", "reflect", "evolve", "think"):
            ok, msg = contract.verify(shift, before)
            self.assertFalse(ok, f"{shift} 班 ledger 没变却过了 —— 思考税漏了")
            if shift != "think":
                self.assertIn("思考税", msg, f"{shift} 班该报思考税未缴")

    def test_watch_is_exempt(self):
        """巡检班的活就是'确认无事发生' —— 唯一免税的班。"""
        before = contract.snapshot()
        ok, _ = contract.verify("watch", before)
        self.assertTrue(ok)

    def test_killing_an_idea_also_pays_the_tax(self):
        """WIP 满了也交得起税: **杀掉一个想法, 和提出一个想法, 都是思考的证据。**

        (契约必须**物理可满足** —— 伤疤 #4: 不可满足的契约不是压力, 是墙。)
        """
        before = contract.snapshot()
        contract.LEDGER.write_text('{"id":1,"status":"killed"}\n')   # 只是杀了一个, 没提新的
        ok, msg = contract.verify("reflect", before)
        self.assertNotIn("思考税", msg, "杀死一个想法必须算交税")


class AttributionGate(unittest.TestCase):
    """伤疤 #8 的核心断言: trailer 计数只认 `Founder-OS-Shift:` 行首 trailer。"""

    def test_plain_mention_does_not_count(self):
        """伤疤 #6: 'grep 到字符串' ≠ '真的有归因'。正文提到 founder-os 不算。"""
        with tempfile.TemporaryDirectory() as td:
            subprocess.run(["git", "init", "-q", td], check=True)
            def commit(msg):
                subprocess.run(["git", "-C", td, "commit", "-q", "--allow-empty",
                                "-m", msg, "-c" if False else "--no-gpg-sign"],
                               env={"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                                    "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
                                    "PATH": "/usr/bin:/bin:/usr/local/bin"}, check=True)
            commit("docs: mention founder-os in passing")           # 只提到, 不是 trailer
            r = subprocess.run(["git", "-C", td, "log", "--grep=^Founder-OS-Shift:",
                                "--extended-regexp", "--oneline"], capture_output=True, text=True)
            self.assertEqual(r.stdout.strip(), "", "正文提到不该算归因")
            commit("real work\n\nFounder-OS-Shift: build")          # 真 trailer
            r = subprocess.run(["git", "-C", td, "log", "--grep=^Founder-OS-Shift:",
                                "--extended-regexp", "--oneline"], capture_output=True, text=True)
            self.assertEqual(len(r.stdout.strip().splitlines()), 1, "真 trailer 必须被认出")


class FitnessFailsLoud(unittest.TestCase):
    """「失败要吵, 不要静」—— 拒绝把 None 写进适应度历史。

    伤疤: 空气比没有更糟 —— 一个记满 None 的历史会让进化班以为"有数据", 让所有人停止追查。
    """

    def setUp(self):
        sys.path.insert(0, str(ROOT / "src"))
        import fitness
        self.f = fitness
        self.tmp = tempfile.TemporaryDirectory()
        self._orig = (fitness.GOAL, fitness.HIST)
        fitness.GOAL = Path(self.tmp.name) / "GOAL.md"
        fitness.HIST = Path(self.tmp.name) / "fitness.jsonl"

    def tearDown(self):
        self.f.GOAL, self.f.HIST = self._orig
        self.tmp.cleanup()

    def test_placeholder_is_not_config(self):
        """模板占位符 ≠ 已配置。(「声明≠有效」)"""
        self.f.GOAL.write_text("FITNESS_CMD=（填写, 没有就留空）\nFITNESS_DIRECTION=higher\n")
        with self.assertRaises(SystemExit):
            self.f.record(None)
        self.assertFalse(self.f.HIST.exists(), "拒绝时不该留下垃圾历史")

    def test_command_yielding_no_number_is_refused(self):
        """命令跑了但抠不出数 → 拒绝记录, 不写 None。"""
        self.f.GOAL.write_text("FITNESS_CMD=echo no-number-here\nFITNESS_DIRECTION=higher\n")
        with self.assertRaises(SystemExit):
            self.f.record(None)
        self.assertFalse(self.f.HIST.exists())

    def test_real_number_is_recorded(self):
        """真给出数 → 正常记录。"""
        self.f.GOAL.write_text("FITNESS_CMD=echo 42\nFITNESS_DIRECTION=higher\n")
        self.f.record(None)
        rec = json.loads(self.f.HIST.read_text().splitlines()[0])
        self.assertEqual(rec["value"], 42.0)


class BaselineDifferencing(unittest.TestCase):
    """归因门 v3 的核心断言: **可归因 ≠ 有效; 接触 ≠ 贡献。**

    验尸案由: 一份从没运行过的代码 + 一个 trailer, 在 v2 下拿走了赛道的
    全部继承净值 ($8312.22)。v3 之后, 同样的操作只能拿 0。
    """

    def test_untouched_track_scores_zero(self):
        """从未归因 → 0 分, 不管赛道净值多高 (v2 已有, v3 必须保住)。"""
        r = fitness_bridge.compute(8312.22, 3, anchor=None, fresh=False,
                                   base_money=None, base_shipped=None)
        self.assertEqual(r["fitness"], 0.0)
        self.assertEqual(r["attributable"], 0)

    def test_stale_attribution_scores_zero(self):
        """idea #6: 曾经归因 ≠ 现在归因。30 天窗外 → 0 分。"""
        r = fitness_bridge.compute(8312.22, 3, anchor="abc123", fresh=False,
                                   base_money=100.0, base_shipped=0)
        self.assertEqual(r["fitness"], 0.0)
        self.assertEqual(r["attributable"], 0)

    def test_inherited_level_is_not_contribution(self):
        """验尸案本尊: 首次归因时, 分数必须是 0, 不是继承电平 8312.22。"""
        r = fitness_bridge.compute(8312.22, 3, anchor="abc123", fresh=True,
                                   base_money=8312.22, base_shipped=3)
        self.assertEqual(r["fitness"], 0.0, "接触本身必须发 0 分, 不是发电平")
        self.assertEqual(r["shipped_delta"], 0, "epoch 前就 live 的策略不是我们的产出")

    def test_only_post_epoch_change_counts(self):
        """epoch 之后赛道真的变了 → 只有变化量计入。"""
        r = fitness_bridge.compute(8500.00, 4, anchor="abc123", fresh=True,
                                   base_money=8312.22, base_shipped=3)
        self.assertAlmostEqual(r["fitness"], 187.78, places=2)
        self.assertEqual(r["shipped_delta"], 1)
        self.assertNotAlmostEqual(r["fitness"], 8500.00, places=2,
                                  msg="电平绝不允许再漏出来")

    def test_missing_baseline_fails_loud(self):
        """归因成立但基线算不出 → 必须吵 (RuntimeError), 禁止静默发分或发 0 装清白。"""
        with self.assertRaises(RuntimeError):
            fitness_bridge.compute(8312.22, 3, anchor="abc123", fresh=True,
                                   base_money=None, base_shipped=None)


class WallsLedger(unittest.TestCase):
    """墙账本 (idea #7) — **WALL ≠ LAZY**。

    验尸案由: 一堵权限墙被撞了 3 次, 解封动作 (一行配置) 每次都写进 journal 散文,
    **人一次没读**。它挡住的装置在解封后的第一次运行, 就打穿了实盘策略的毕业证据。
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        import walls
        self.w = walls
        self._orig = walls.WALLS
        walls.WALLS = Path(self.tmp.name) / "walls.jsonl"

    def tearDown(self):
        self.w.WALLS = self._orig
        self.tmp.cleanup()

    def _ns(self, **kw):
        base = {"wall": "w", "fix": "一行解法", "blocked": "某产出",
                "shift": "think", "note": None}
        base.update(kw)
        return type("A", (), base)()

    def test_new_wall_without_a_one_line_fix_is_rejected(self):
        """没有解法的墙, 对人来说只是一句抱怨 —— 而抱怨会被跳过。"""
        with self.assertRaises(SystemExit):
            self.w.hit(self._ns(fix=None))
        self.assertEqual(self.w.standing(), [])

    def test_rehitting_the_same_wall_raises_its_priority(self):
        """撞击次数 = 优先级。第 4 次撞同一堵墙, 必须比第 1 次更响。"""
        self.w.hit(self._ns())
        self.w.hit(self._ns(fix=None, note="又撞了"))   # 老墙无需再给 fix
        self.assertEqual(len(self.w.standing()), 1, "同一堵墙不该开出第二行")
        self.assertEqual(self.w.standing()[0]["hits"], 2)
        self.assertEqual(len(self.w.standing()[0]["hit_log"]), 2, "每次撞击都要留证")

    def test_agent_cannot_declare_a_wall_torn_down(self):
        """agent 自己宣布'墙拆了' = 自己给自己发赦免: 墙还立着, 账本却说没事了。

        (亲证: 账本上线第一天, 就有人把一堵**没拆的**墙标成了 torn_down。)
        """
        self.w.hit(self._ns())
        os.environ.pop("FOUNDER_HUMAN", None)
        with self.assertRaises(SystemExit):
            self.w.down(type("A", (), {"id": 1})())
        self.assertEqual(len(self.w.standing()), 1, "墙必须还立着")


class PermissionsActuallyMatch(unittest.TestCase):
    """**权限写了 ≠ 权限能匹配到你真要跑的命令。** (「声明≠有效」的第 8 张脸)

    验尸案由: 人照着 agent 的解封提示加权限, 但把绝对路径顺手写成了相对路径:
        "Bash(./.venv/bin/python research/:*)"
    它写进了配置、看起来完全合理、**而班次的 cwd 是 founder-os** —— 那里既没有 .venv
    也没有 research/。这条 allow **永远匹配不上任何真实命令**。
    墙还立着, 配置却显示"已放行", 而账本被标成了"已解决"。
    """

    def setUp(self):
        import preflight
        self.p = preflight

    def test_relative_allow_does_not_cover_the_absolute_track_command(self):
        """就是那个 bug 本身。"""
        allow = ["Bash(./.venv/bin/python research/:*)", "Bash(python3 research/:*)"]
        cmd = "/Users/x/trading/.venv/bin/python research/foo.py"
        self.assertFalse(self.p._covers(cmd, allow),
                         "相对路径的 allow 绝不允许再被当成'已放行'")

    def test_absolute_allow_covers_it(self):
        allow = ["Bash(/Users/x/trading/.venv/bin/python:*)"]
        self.assertTrue(self.p._covers("/Users/x/trading/.venv/bin/python research/foo.py", allow))

    def test_garage_git_does_not_cover_track_git(self):
        """伤疤 #8 在权限层: 班次 cwd = 车库, 裸 `git commit` 提交的是**车库**。

        而 build 契约要的是**赛道上带 trailer 的 commit**。两者永远对不上。
        """
        self.assertFalse(self.p._covers("git -C /Users/x/trading commit", ["Bash(git commit:*)"]))
        self.assertTrue(self.p._covers("git -C /Users/x/trading commit",
                                       ["Bash(git -C /Users/x/trading:*)"]))

    def test_exact_form_is_not_a_prefix(self):
        """`Bash(X)` 是精确匹配, 不是前缀 —— 别把它当成放行了一族命令。"""
        self.assertTrue(self.p._covers("git status", ["Bash(git status)"]))
        self.assertFalse(self.p._covers("git status -s", ["Bash(git status)"]))


if __name__ == "__main__":
    unittest.main()
