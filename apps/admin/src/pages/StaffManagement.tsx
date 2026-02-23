import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';


export default function StaffManagement() {
    return (
        <div className="space-y-6">
            <h1 className="text-3xl font-bold">Staff & Availability</h1>
            <Card>
                <CardHeader>
                    <CardTitle>Specialists Ledger</CardTitle>
                </CardHeader>
                <CardContent>
                    <p className="text-gray-500">Master management table coming soon...</p>
                </CardContent>
            </Card>
        </div>
    );
}
