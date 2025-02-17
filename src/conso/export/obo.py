# -*- coding: utf-8 -*-

"""Export the Curation of Neurodegeneration Supporting Ontology (CONSO) to OBO."""

import csv
from typing import Dict, Iterable, List, Mapping, Tuple

import click

from pyobo import Obo, Reference, Synonym, Term, TypeDef
from pyobo.struct.typedef import has_role, part_of
from ..resources import AUTHORS_PATH, RELATIONS_PATH, SYNONYMS_PATH, TERMS_PATH, TYPEDEF_PATH, XREFS_PATH

CONSO = 'CONSO'


def get_obo() -> Obo:
    """Get OBO object."""
    terms, typedefs = get_content()
    return Obo(
        format_version='1.2',
        auto_generated_by='https://github.com/pharmacome/conso/blob/master/src/conso/export/obo.py',
        ontology='conso',
        name='Curation of Neurodegeneration Supporting Ontology',
        iter_terms=lambda: iter(terms),
        typedefs=typedefs,
    )


def _extract_references(s: str) -> Iterable[Reference]:
    for curie in s.split(','):
        reference = Reference.from_curie(curie)
        if reference is not None:
            yield reference


def get_content() -> Tuple[List[Term], List[TypeDef]]:
    """Iterate CONSO terms."""
    with open(TYPEDEF_PATH) as file:
        reader = csv.reader(file, delimiter='\t')
        _ = next(reader)  # skip the header
        typedefs: Dict[str, TypeDef] = {
            identifier: TypeDef(
                reference=Reference(prefix=CONSO, identifier=identifier, name=name),
                namespace=namespace,
                xrefs=list(_extract_references(xrefs)),
                is_transitive=transitive == 'true',
                comment=comment,
            )
            for identifier, name, namespace, xrefs, transitive, comment in reader
        }
        typedefs.update(part_of=part_of, has_role=has_role)
        del typedefs['bel']

    with open(AUTHORS_PATH) as file:
        reader = csv.reader(file, delimiter='\t')
        _ = next(reader)  # skip the header
        authors: Mapping[str, Reference] = {
            orcid_identifier: Reference(
                prefix='orcid',
                identifier=orcid_identifier,
                name=author,
            )
            for orcid_identifier, author in reader
        }

    with open(TERMS_PATH) as file:
        reader = csv.reader(file, delimiter='\t')
        _ = next(reader)  # skip the header

        terms: Dict[str, Term] = {}
        for conso_id, author_key, name, namespace, references, description in reader:
            if name == 'WITHDRAWN':
                continue
            terms[conso_id] = Term(
                reference=Reference(
                    prefix=CONSO,
                    identifier=conso_id,
                    name=name,
                ),
                provenance=list(_extract_references(references)),
                namespace=namespace,
                definition=description,
            )
            terms[conso_id].relationships[typedefs['author']].append(authors[author_key])

    with open(SYNONYMS_PATH) as file:
        reader = csv.reader(file, delimiter='\t')
        _ = next(reader)  # skip the header
        for conso_id, synonym, references, specificity in reader:
            references = (
                [r.strip() for r in references.split(',')]
                if references and references != '?' else
                []
            )
            specificity = (
                'EXACT' if specificity == '?' else specificity
            )
            terms[conso_id].synonyms.append(Synonym(synonym, specificity, provenance=references))

    with open(XREFS_PATH) as file:
        reader = csv.reader(file, delimiter='\t')
        _ = next(reader)  # skip the header
        for conso_id, database, identifier in reader:
            if database.lower() == 'bel':
                terms[conso_id].append_property('bel', identifier)
            else:
                terms[conso_id].append_xref(Reference(prefix=database, identifier=identifier))

    with open(RELATIONS_PATH) as file:
        reader = enumerate(csv.reader(file, delimiter='\t'), start=1)
        _ = next(reader)  # skip the header
        handled_relations = {'is_a'} | set(typedefs)
        for line, (source_ns, source_id, _source_name, relation, target_ns, target_id, target_name) in reader:
            if relation not in handled_relations:
                print(f'{RELATIONS_PATH} can not handle line {line} because unhandled relation: {relation}')
                continue

            if source_ns != CONSO and target_ns != CONSO:
                print(f'{RELATIONS_PATH}: skipping line {line} because neither entity is from {CONSO}')
                continue

            if source_ns != CONSO:
                print(f'{RELATIONS_PATH} can not handle line {line} because of'
                      f' inverse relation definition to external identifier')
                continue

            target = Reference(prefix=target_ns, identifier=target_id, name=target_name)
            if relation == 'is_a':
                terms[source_id].append_parent(target)
            else:
                terms[source_id].append_relationship(typedefs[relation], target)

    return list(terms.values()), list(typedefs.values())


@click.command()
@click.argument('path')
@click.option('--check', is_flag=True)
def obo(path: str, check: bool):
    """Export CONSO as OBO."""
    get_obo().write_obo(path)

    if check:
        import obonet
        obonet.read_obo(path)


if __name__ == '__main__':
    obo()
