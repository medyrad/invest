import CoreShell from '@/components/core/shell';
import {TopicList} from '@/components/guide/library';
import {libraryTopics,libraryIntro} from '@/data/library';
export default function Page(){return <CoreShell><h1>راهنما و مستندات</h1><p>{libraryIntro}</p><TopicList topics={libraryTopics}/></CoreShell>}
