from __future__ import print_function

from prettytable import ALL, PrettyTable

from kube_hunter.conf import config
from kube_hunter.modules.report.base import BaseReporter
from kube_hunter.modules.report.collector import services, vulnerabilities, hunters, services_lock, vulnerabilities_lock

EVIDENCE_PREVIEW = 40
MAX_TABLE_WIDTH = 20
KB_LINK = "https://github.com/aquasecurity/kube-hunter/tree/master/docs/kb"


class PlainReporter(BaseReporter):

    def get_report(self):
        """generates report tables"""
        output = ""

        with vulnerabilities_lock:
            vulnerabilities_len = len(vulnerabilities)

        hunters_len = len(hunters.items())

        with services_lock:
            services_len = len(services)

        if services_len:
            output += self.nodes_table()
            if not config.mapping:
                output += self.services_table()
                if vulnerabilities_len:
                    output += self.vulns_table()
                else:
                    output += "\nNo vulnerabilities were found"
                if config.statistics:
                    if hunters_len:
                        output += self.hunters_table()
                    else:
                        output += "\nNo hunters were found"
        else:
            if vulnerabilities_len:
                output += self.vulns_table()
            output += "\nKube Hunter couldn't find any clusters"
            # print("\nKube Hunter couldn't find any clusters. {}".format("Maybe try with --active?" if not config.active else ""))
        return output

    def nodes_table(self):
        nodes_table = PrettyTable(["Type", "Location"], hrules=ALL)
        nodes_table.align = "l"
        nodes_table.max_width = MAX_TABLE_WIDTH
        nodes_table.padding_width = 1
        nodes_table.sortby = "Type"
        nodes_table.reversesort = True
        nodes_table.header_style = "upper"
        id_memory = set()
        services_lock.acquire()
        for service in services:
            if service.event_id not in id_memory:
                nodes_table.add_row(["Node/Master", service.host])
                id_memory.add(service.event_id)
        nodes_ret = "\nNodes\n{}\n".format(nodes_table)
        services_lock.release()
        return nodes_ret

    def services_table(self):
        services_table = PrettyTable(["Service", "Location", "Description"], hrules=ALL)
        services_table.align = "l"
        services_table.max_width = MAX_TABLE_WIDTH
        services_table.padding_width = 1
        services_table.sortby = "Service"
        services_table.reversesort = True
        services_table.header_style = "upper"
        with services_lock:
            for service in services:
                services_table.add_row([service.get_name(), "{}:{}{}".format(service.host, service.port, service.get_path()), service.explain()])
            detected_services_ret = "\nDetected Services\n{}\n".format(services_table)
        return detected_services_ret

    def vulns_table(self):
        column_names = ["ID", "Location", "Category", "Vulnerability", "Description", "Evidence"]
        vuln_table = PrettyTable(column_names, hrules=ALL)
        vuln_table.align = "l"
        vuln_table.max_width = MAX_TABLE_WIDTH
        vuln_table.sortby = "Category"
        vuln_table.reversesort = True
        vuln_table.padding_width = 1
        vuln_table.header_style = "upper"

        with vulnerabilities_lock:
            for vuln in vulnerabilities:
                evidence = str(vuln.evidence)[:EVIDENCE_PREVIEW] + "..." if len(str(vuln.evidence)) > EVIDENCE_PREVIEW else str(vuln.evidence)
                row = [vuln.get_vid(), vuln.location(), vuln.category.name, vuln.get_name(), vuln.explain(), evidence]
                vuln_table.add_row(row)
        return "\nVulnerabilities\nFor further information about a vulnerability, search its ID in: \n{}\n{}\n".format(KB_LINK, vuln_table)

    def hunters_table(self):
        column_names = ["Name", "Description", "Vulnerabilities"]
        hunters_table = PrettyTable(column_names, hrules=ALL)
        hunters_table.align = "l"
        hunters_table.max_width = MAX_TABLE_WIDTH
        hunters_table.sortby = "Name"
        hunters_table.reversesort = True
        hunters_table.padding_width = 1
        hunters_table.header_style = "upper"

        hunter_statistics = self.get_hunter_statistics()
        for item in hunter_statistics:
            hunters_table.add_row([item.get("name"), item.get("description"), item.get("vulnerabilities")])
        return "\nHunter Statistics\n{}\n".format(hunters_table)
